from flask import Flask, render_template, Markup, flash
from flask_socketio import SocketIO
from time import mktime
from datetime import datetime
import sqlite3

## Number of seconds between sending new sentiment/emotional data to socket:
DATA_WAIT = 10
###

app = Flask(__name__)
app.secret_key = b')\x9c\xc7\xa7\xb3\xd2\xa9\x8ch\xd6\xc9\xfc\xe6g!c'
socketio = SocketIO(app, async_mode='eventlet')
update_vals = None


def update_thread():
    while True:
        for data in all_data:
            socketio.emit('update-vr',
                          {'tweet': data[0],
                             'sentiment': data[1],
                             'joy': data[2],
                             'anger': data[3],
                             'disgust': data[4],
                             'sadness': data[5],
                             'fear': data[6]}, namespace='/graphSock')
            print("sending %s, %s, %s, %s, %s, %s, %s" % data[0:7])
            socketio.sleep(DATA_WAIT)


@app.route('/vr')
def candle():
    candle_file = 'vr.html'
    return render_template(candle_file, async_mode=socketio.async_mode,
                           sentiment_list=all_data)


@socketio.on('connect', namespace='/graphSock')
def connect():
    global update_vals
    if update_vals is None:
        update_vals = socketio.start_background_task(target=update_thread)
    data = all_data[0]
    socketio.emit('update-vr',
                  {'tweet': data[0],
                   'sentiment': data[1],
                   'joy': data[2],
                   'anger': data[3],
                   'disgust': data[4],
                   'sadness': data[5],
                   'fear': data[6]}, namespace='/graphSock')


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