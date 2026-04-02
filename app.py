from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
import uuid
import time
import threading
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ghostchat-secret-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# In-memory storage (ephemeral - all data lost on restart)
rooms = {}  # room_id -> {messages: [], users: set(), created_at: timestamp}

def cleanup_empty_rooms():
    """Background task to clean up empty rooms"""
    while True:
        time.sleep(30)
        empty = [rid for rid, r in list(rooms.items()) if len(r['users']) == 0]
        for rid in empty:
            rooms.pop(rid, None)

# Start background cleanup
cleanup_thread = threading.Thread(target=cleanup_empty_rooms, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create_room():
    room_id = str(uuid.uuid4())[:8].upper()
    rooms[room_id] = {
        'messages': [],
        'users': set(),
        'created_at': time.time()
    }
    return redirect(url_for('chat', room_id=room_id))

@app.route('/join', methods=['POST'])
def join():
    room_id = request.form.get('room_id', '').strip().upper()
    if not room_id:
        return redirect(url_for('index'))
    if room_id not in rooms:
        rooms[room_id] = {
            'messages': [],
            'users': set(),
            'created_at': time.time()
        }
    return redirect(url_for('chat', room_id=room_id))

@app.route('/chat/<room_id>')
def chat(room_id):
    room_id = room_id.upper()
    if room_id not in rooms:
        rooms[room_id] = {
            'messages': [],
            'users': set(),
            'created_at': time.time()
        }
    return render_template('chat.html', room_id=room_id)

# --- Socket.IO Events ---

@socketio.on('join')
def on_join(data):
    room_id = data['room'].upper()
    username = data.get('username', 'Anonymous')
    sid = request.sid

    join_room(room_id)

    if room_id not in rooms:
        rooms[room_id] = {'messages': [], 'users': set(), 'created_at': time.time()}

    rooms[room_id]['users'].add(sid)

    # Send existing messages to the new joiner
    emit('history', {'messages': rooms[room_id]['messages']})

    # Notify others
    emit('system', {
        'text': f'{username} joined the ghost room',
        'count': len(rooms[room_id]['users'])
    }, to=room_id)

@socketio.on('message')
def on_message(data):
    room_id = data['room'].upper()
    username = data.get('username', 'Anonymous')
    text = data.get('text', '').strip()

    if not text or room_id not in rooms:
        return

    msg = {
        'id': str(uuid.uuid4()),
        'username': username,
        'text': text,
        'timestamp': time.time(),
        'time_str': time.strftime('%H:%M')
    }

    rooms[room_id]['messages'].append(msg)

    emit('message', msg, to=room_id)

@socketio.on('typing')
def on_typing(data):
    room_id = data['room'].upper()
    username = data.get('username', '')
    emit('typing', {'username': username}, to=room_id, include_self=False)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    for room_id, room in list(rooms.items()):
        if sid in room['users']:
            room['users'].discard(sid)
            user_count = len(room['users'])

            # If room is empty, wipe all messages (ephemeral!)
            if user_count == 0:
                room['messages'] = []
                emit('cleared', {'reason': 'All users left. Messages wiped.'}, to=room_id)
            else:
                emit('system', {
                    'text': 'A user left the ghost room',
                    'count': user_count
                }, to=room_id)

if __name__ == '__main__':
    
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port, use_reloader=False)
