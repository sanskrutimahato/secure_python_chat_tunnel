import sqlite3
import os
import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google import genai

# Load environment variables
load_dotenv()

# Get API Key
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found! Check your .env file.")

ai_client = genai.Client(api_key=API_KEY)
app = FastAPI()

# --- 1. STATIC FILES ---
app.mount("/static", StaticFiles(directory="."), name="static")

# --- 2. DATABASE SETUP ---
def get_db():
    """Creates a fresh DB connection per call — safe for concurrent users."""
    conn = sqlite3.connect('chat_history.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Create table once on startup
with get_db() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            message TEXT
        )
    ''')
    conn.commit()

# --- 3. SERVE THE FRONTEND ---
@app.get("/")
async def get():
    with open("index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(html_content)

# --- 4. CONNECTION MANAGER ---
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

    def count(self):
        return len(self.active_connections)

manager = ConnectionManager()

# --- 5. WEBSOCKET & COMMAND LOGIC ---
@app.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    await manager.connect(websocket)

    # Send past chat history to the newly connected user
    with get_db() as conn:
        rows = conn.execute("SELECT sender, message FROM messages").fetchall()
    for row in rows:
        await websocket.send_text(f"{row['sender']}: {row['message']}")

    # Announce join with current online count
    await manager.broadcast(f"System: {client_name} joined — {manager.count()} users online")

    try:
        while True:
            data = await websocket.receive_text()

            # Save and broadcast user message
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO messages (sender, message) VALUES (?, ?)",
                    (client_name, data)
                )
                conn.commit()
            await manager.broadcast(f"{client_name}: {data}")

            # --- COMMAND ROUTER ---
            if data.startswith("!"):
                parts = data[1:].split(" ", 1)
                command = parts[0].lower()
                bot_reply = ""

                if command == "time":
                    bot_reply = f"Bot: The current server time is {datetime.datetime.now().strftime('%H:%M:%S')}."

                elif command == "stats":
                    with get_db() as conn:
                        count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
                    bot_reply = f"Bot: Total messages sent: {count}."

                elif command == "users":
                    bot_reply = f"Bot: There are {manager.count()} users online right now."

                elif command == "help":
                    bot_reply = "Bot: Commands: !time, !stats, !users, !help, or ![anything] for AI."

                # AI fallback for unknown commands
                else:
                    try:
                        prompt = f"User {client_name} asked: '{data[1:]}'. Reply in 1 short sentence."
                        response = await ai_client.aio.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt
                        )
                        bot_reply = f"Bot: {response.text}"
                    except Exception as e:
                        bot_reply = "Bot: (AI Error) Try !time, !stats, or !users instead."

                # Save and broadcast bot reply
                if bot_reply:
                    with get_db() as conn:
                        conn.execute(
                            "INSERT INTO messages (sender, message) VALUES (?, ?)",
                            ("Bot", bot_reply.replace("Bot: ", ""))
                        )
                        conn.commit()
                    await manager.broadcast(bot_reply)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"System: {client_name} left — {manager.count()} users online")