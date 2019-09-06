from flask import Flask, render_template, Markup, flash
from flask_socketio import SocketIO
from time import mktime
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = b')\x9c\xc7\xa7\xb3\xd2\xa9\x8ch\xd6\xc9\xfc\xe6g!c'
socketio = SocketIO(app, async_mode='eventlet')

@app.route('/candle')
def candle():
    candle_file = 'candle.html'
    return render_template(candle_file, async_mode=socketio.async_mode,
                           sentiment_list=all_data)

if __name__ == '__main__':
    print('getting fear...')
    con = sqlite3.connect('db/graphs_db.db')
    cursor = con.cursor()

    all_data = []

    cursor.execute('''SELECT date,
                             hour,
                             MAX(fear),
                             MIN(fear)
                        FROM twitter
                        GROUP BY date,
                             hour''')
    new_cursor = con.cursor()
    now = datetime.today()
    for row in cursor:
        now -= timedelta(hours=1)
        timestamp = mktime(now.timetuple())
        new_cursor.execute('''SELECT fear
                            FROM twitter
                            WHERE date=? AND hour=?''', (row[0], row[1]))
        sentiments = new_cursor.fetchall()
        opening = sentiments[0][0]
        closing = sentiments[-1][0]
        high = row[2]
        low = row[3]
        all_data.append([int(timestamp), [opening, high, low, closing]])

    print(all_data)
    print('starting app')
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True)