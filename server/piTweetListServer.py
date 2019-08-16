from flask import Flask, render_template, Markup, flash
from flask_socketio import SocketIO
from time import mktime
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = b')\x9c\xc7\xa7\xb3\xd2\xa9\x8ch\xd6\xc9\xfc\xe6g!c'
socketio = SocketIO(app, async_mode='eventlet')
update_vals = None
DATA_WAIT = 2

def update_thread():
    while True:
        socketio.emit('update-tweets', {}, namespace='/graphSock')
        socketio.sleep(DATA_WAIT)

@socketio.on('connect', namespace='/graphSock')
def connect():
    global update_vals
    # if update_vals is None:
    #     update_vals = socketio.start_background_task(target=update_thread)

@app.route('/tweet_top')
def tweet():
    tweet_file = 'tweet.html'
    return render_template(tweet_file, async_mode=socketio.async_mode,
                           initial_data=all_data)

if __name__ == '__main__':
    print('getting data...')
    con = sqlite3.connect('db/graphs_db.db')
    cursor = con.cursor()

    cursor.execute('''SELECT tweet,
                             sentiment,
                             joy,
                             anger,
                             disgust,
                             sadness,
                             fear
                        FROM twitter''')

    all_data = cursor.fetchall()

    print('starting app')
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True)