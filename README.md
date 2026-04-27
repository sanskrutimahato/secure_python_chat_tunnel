# 🟣 Twitch-Style AI Chat

A full-stack, real-time chat application with a hybrid command engine — local instant commands and cloud AI responses via Google Gemini, served publicly through a Cloudflare Tunnel.

---

## ✨ Features

- **Real-Time Messaging** — WebSocket-powered chat via FastAPI; no page refreshes needed.
- **Persistent History** — SQLite3 stores messages and reloads them automatically when a user joins.
- **Hybrid Bot Engine** — Local commands run instantly on your CPU; unknown `!commands` are routed to Gemini 2.5 Flash.
- **Mirror UI** — Dark mode layout where your messages appear on the right (indigo) and the bot's on the left (green).
- **Secure by Default** — API keys stored in `.env`; public access via an encrypted Cloudflare Tunnel.

---

## 🛠️ Tech Stack

| Component     | Technology                          |
|---------------|-------------------------------------|
| Language      | Python 3                            |
| Framework     | FastAPI (Asynchronous)              |
| Database      | SQLite3 (Persistent)               |
| AI Model      | Gemini 2.5 Flash (Google GenAI SDK) |
| Frontend      | HTML5 / CSS3 (Bootstrap) / Vanilla JS |
| Proxy/Tunnel  | Cloudflare Tunnels (Reverse Proxy)  |

---

## 🤖 Commands

| Input            | Type     | Result                              |
|------------------|----------|-------------------------------------|
| `!time`          | Local    | Shows server clock (instant)        |
| `!stats`         | Local    | Shows DB message count (instant)    |
| `!help`          | Local    | Lists all commands (instant)        |
| `!users`         | Local    | Shows active user count (instant)   |
| `![anything else]` | Cloud AI | Sent to Gemini 2.5 Flash (1–2s delay) |

---

## 🚀 Getting Started (Restart Guide)

Follow these steps every time you need to go live after closing your laptop.

### Step 1 — Navigate and activate the environment

```bash
cd ~/group_chat_project
source venv/bin/activate
```

### Step 2 — Start the backend (Terminal 1)

```bash
uvicorn main:app --reload
```

Keep this terminal open. Wait until you see:
```
Application startup complete.
```

### Step 3 — Open the public tunnel (Terminal 2)

Open a new tab (`Ctrl+Shift+T`) and run:

```bash
cloudflared tunnel --url http://localhost:8000
```

Scroll up in the output to find a link ending in `.trycloudflare.com`. Copy it and share with teammates or open on your phone.

---

## 🧪 Testing the Deployment

1. Paste the `.trycloudflare.com` link into any browser (mobile or PC).
2. Enter a display name — names are **case-sensitive** for the Mirror UI logic.
3. Run the success checks:
   - `!time` → Server clock should respond instantly.
   - `!stats` → Should show the correct message count from the DB.
   - Your message bubble should appear **indigo on the right**; bot bubbles should be **green on the left**.

---

## 🔧 Maintenance

**Inspect the database manually:**
```bash
sqlite3 chat_history.db
```

**Reinstall dependencies if something is missing:**
```bash
pip install python-dotenv google-genai fastapi uvicorn
```

**Security reminder:** Never delete or share your `.env` file — it contains your Gemini API key.

## 🏗️ Architecture

```
Browser / Mobile Client
        │
        │  WebSocket + HTTP
        ▼
   FastAPI Backend  ──── SQLite3 (chat_history.db)
        │
        ├── Local Commands (!time, !stats, !help, !users)
        │         └── Handled instantly on CPU
        │
        └── AI Commands (!anything_else)
                  └── Google Gemini 2.5 Flash API
                            (via .env API key)

Public Access:
   localhost:8000  ──►  cloudflared tunnel  ──►  *.trycloudflare.com
```
🚀 **Project Ownership Note**  
Built as part of a collaborative academic project, this repository showcases a learning-focused implementation of full-stack real-time systems.
