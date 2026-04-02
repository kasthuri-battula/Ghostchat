# 👻 GhostChat — Ephemeral Real-Time Chat App

A WhatsApp/Instagram-style chat app where **messages vanish automatically** when everyone leaves the room.

## ✨ Features
- 🔗 Join via shareable unique room link or code
- 💨 Messages auto-deleted when the room becomes empty
- ⚡ Real-time messaging with Socket.IO (WebSockets)
- 💬 Typing indicators
- 📱 Mobile-friendly responsive design
- 🔐 No accounts, no database, no tracking

---

## 🚀 Setup & Run

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

---

## 📁 Project Structure
```
ghostchat/
├── app.py                  # Flask + Socket.IO backend
├── requirements.txt        # Python dependencies
└── templates/
    ├── index.html          # Landing page (create/join room)
    └── chat.html           # Chat room UI
```

---

## 🔧 How It Works

| Feature | How |
|--------|-----|
| Real-time chat | Flask-SocketIO (WebSockets) |
| Message storage | In-memory Python dict (no DB!) |
| Auto-wipe | Messages deleted when last user disconnects |
| Room creation | Random 8-char UUID room code |
| Sharing | Copy the URL — it includes the room code |

---

## 🌐 Deploy (optional)
To run on a server with a public IP:
```bash
# Install gunicorn + eventlet
pip install gunicorn eventlet

# Run with eventlet worker
gunicorn --worker-class eventlet -w 1 app:app --bind 0.0.0.0:5000
```

> ⚠️ Since storage is in-memory, all rooms/messages reset on server restart.
> For persistent rooms (but still ephemeral messages), you could add Redis.
