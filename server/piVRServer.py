from flask import Flask, render_template, Markup, flash
from flask_socketio import SocketIO
from time import time
from random import randrange, randint
import sqlite3

## Number of seconds between sending new sentiment/emotional data to socket:
DATA_WAIT = 1
###

app = Flask(__name__)
app.secret_key = b')\x9c\xc7\xa7\xb3\xd2\xa9\x8ch\xd6\xc9\xfc\xe6g!c'
socketio = SocketIO(app, async_mode='eventlet')
update_vals = None


def update_thread():
    data_pos = 0
    news_sentiment = 0
    next_tweet = time() + randrange(20, 120)
    while True:
        # news_sentiment = float(randrange(0, 9999) / 10000)
        if 0 <= news_sentiment <= 1:
            news_sentiment += 0.1
        else:
            news_sentiment = 0
        # news_sentiment = float(randint(0, 9999) / 10000)
        print("new sentiment = %s" % news_sentiment)
        socketio.emit('update-vr-news',
                      {'news': 'This is a test headline...%s' % time(),
                       'sentiment': news_sentiment},
                      namespace='/graphSock')
        if time() > next_tweet:
            data = all_data[data_pos]
            socketio.emit('update-vr-tweet',
                          {'tweet': data[0],
                             'sentiment': data[1],
                             'joy': data[2],
                             'anger': data[3],
                             'disgust': data[4],
                             'sadness': data[5],
                             'fear': data[6]}, namespace='/graphSock')
            print("sending tweet data")
            data_pos += 1
            next_tweet = time() + randrange(20, 120)
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
    socketio.emit('update-vr-tweet',
                  {'tweet': data[0],
                   'sentiment': data[1],
                   'joy': data[2],
                   'anger': data[3],
                   'disgust': data[4],
                   'sadness': data[5],
                   'fear': data[6]}, namespace='/graphSock')
    news_sentiment = float(randint(0, 9999) / 10000)
    print("new sentiment = %s" % news_sentiment)
    socketio.emit('update-vr-news',
                  {'news': 'This is a test headline...%s' % time(),
                   'sentiment': news_sentiment},
                    namespace='/graphSock')


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