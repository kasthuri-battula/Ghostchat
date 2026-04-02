from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, join_room, emit
import uuid
import time
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ghostchat-secret-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

rooms = {}

def cleanup_empty_rooms():
    while True:
        time.sleep(60)
        now = time.time()
        to_delete = [rid for rid, r in list(rooms.items())
                     if len(r['users']) == 0 and (now - r['created_at']) > 300]
        for rid in to_delete:
            rooms.pop(rid, None)

threading.Thread(target=cleanup_empty_rooms, daemon=True).start()

def make_room(room_id):
    if room_id not in rooms:
        rooms[room_id] = {'messages': [], 'users': set(), 'created_at': time.time()}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create_room():
    room_id = str(uuid.uuid4())[:8].upper()
    make_room(room_id)
    return redirect(url_for('chat', room_id=room_id))

@app.route('/join', methods=['POST'])
def join():
    room_id = request.form.get('room_id', '').strip().upper()
    if not room_id:
        return redirect(url_for('index'))
    make_room(room_id)
    return redirect(url_for('chat', room_id=room_id))

@app.route('/chat/<room_id>')
def chat(room_id):
    room_id = room_id.upper()
    make_room(room_id)
    return render_template('chat.html', room_id=room_id)

@socketio.on('join')
def on_join(data):
    room_id = data['room'].upper()
    username = data.get('username', 'Anonymous')
    sid = request.sid
    make_room(room_id)
    join_room(room_id)
    rooms[room_id]['users'].add(sid)
    emit('history', {'messages': rooms[room_id]['messages']})
    emit('system', {'text': f'{username} joined the ghost room',
                    'count': len(rooms[room_id]['users'])}, to=room_id)

@socketio.on('message')
def on_message(data):
    room_id = data['room'].upper()
    username = data.get('username', 'Anonymous')
    text = data.get('text', '').strip()
    if not text or room_id not in rooms:
        return
    msg = {'id': str(uuid.uuid4()), 'username': username, 'text': text,
           'timestamp': time.time(), 'time_str': time.strftime('%H:%M')}
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
            count = len(room['users'])
            if count == 0:
                room['messages'] = []
                emit('cleared', {}, to=room_id)
            else:
                emit('system', {'text': 'A user left the ghost room', 'count': count}, to=room_id)

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False)
