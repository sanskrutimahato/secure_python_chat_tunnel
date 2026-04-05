import sqlite3
import os
import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from google import genai

# Load environment variables
load_dotenv()

# Get API Key
API_KEY = os.getenv("GEMINI_API_KEY")

# Check if the key actually loaded (This prevents the crash you saw)
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found! Check your .env file.")

ai_client = genai.Client(api_key=API_KEY)
app = FastAPI()
# --- 1. DATABASE SETUP ---
conn = sqlite3.connect('chat_history.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        message TEXT
    )
''')
conn.commit()

# --- 2. SERVE THE FRONTEND ---
@app.get("/")
async def get():
    # Instead of a giant string, we open the index.html file and read it!
    with open("index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(html_content)

# --- 3. CONNECTION MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- 4. WEBSOCKET & COMMAND LOGIC ---
@app.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    await manager.connect(websocket)
    
    # Load past history
    cursor.execute("SELECT sender, message FROM messages")
    for row in cursor.fetchall():
        await websocket.send_text(f"{row[0]}: {row[1]}")

    await manager.broadcast(f"System: {client_name} joined the demo!")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Save and Broadcast user message
            cursor.execute("INSERT INTO messages (sender, message) VALUES (?, ?)", (client_name, data))
            conn.commit()
            await manager.broadcast(f"{client_name}: {data}")
            
            # --- COMMAND ROUTER ---
            if data.startswith("!"):
                parts = data[1:].split(" ", 1)
                command = parts[0].lower()
                user_query = parts[1] if len(parts) > 1 else ""
                bot_reply = ""

                # Fixed System Commands
                if command == "time":
                    bot_reply = f"Bot: The current server time is {datetime.datetime.now().strftime('%H:%M:%S')}."
                
                elif command == "stats":
                    cursor.execute("SELECT COUNT(*) FROM messages")
                    count = cursor.fetchone()[0]
                    bot_reply = f"Bot: Total messages sent in this demo: {count}."
                
                elif command == "help":
                    bot_reply = "Bot: Commands: !time, !stats, !help, or ![message] for AI."

                # AI Fallback
                else:
                    try:
                        prompt = f"User {client_name} asked: '{data[1:]}'. Reply in 1 short sentence."
                        response = await ai_client.aio.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        bot_reply = f"Bot: {response.text}"
                    except Exception as e:
                        bot_reply = "Bot: (AI Error) System commands (!time, !stats) are still working."

                # Save & Broadcast Bot Reply
                if bot_reply:
                    cursor.execute("INSERT INTO messages (sender, message) VALUES (?, ?)", ("Bot", bot_reply.replace("Bot: ", "")))
                    conn.commit()
                    await manager.broadcast(bot_reply)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"System: {client_name} left the chat")