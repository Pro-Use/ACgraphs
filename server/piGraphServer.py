from flask import Flask, render_template, Markup, flash
from flask_socketio import SocketIO
from time import sleep
import feedparser
from threading import Thread


app = Flask(__name__)
app.secret_key = b')\x9c\xc7\xa7\xb3\xd2\xa9\x8ch\xd6\xc9\xfc\xe6g!c'
socketio = SocketIO(app, async_mode='eventlet')

HEADLINE = "'Despicable act': May confronts Putin over Salisbury poisoning. Church of England appoints its first black female bishop. I felt the fear of abduction by China in Hong Kong. Appeasing Bejing has to stop"
HEADLINE = HEADLINE.replace(' ', '&nbsp;')
RSS = ["http://feeds.bbci.co.uk/news/rss.xml"]
TICKERS = len(RSS)
ticker_html = [""] * len(RSS)
update_feeds = None

def get_news_html(feed):
    news_feed = feedparser.parse(feed)
    if 'title' in news_feed.entries[1].keys():
        html_content = ""
        for entry in news_feed.entries:
            html_content += '<div class="ti_news">%s | </div>\n' % entry.title.replace(' ', '&nbsp;')
        return html_content
    else:
        return None

def update_thread(tickers):
    global ticker_html
    socketio.sleep(3)
    while True:
        print("updating feeds")
        for i in range(0, tickers):
            ticker = i
            new_html = get_news_html(RSS[ticker])
            if new_html is not None:
                ticker_html[ticker] = new_html
                socketio.emit('update', {'ticker':ticker, 'html': new_html}, namespace='/graphSock')
        socketio.sleep(1800)



@app.route('/news_left')
def left():
    left_file = 'news.html'
    for n in range(0, len(ticker_html)):
        ticker_html[n] = Markup(ticker_html[n])
    return render_template(left_file, async_mode=socketio.async_mode, position=0, tickers=TICKERS, html=ticker_html)


@app.route('/news_right')
def right():
    right_file = 'news.html'
    for n in range(0, len(ticker_html)):
        ticker_html[n] = Markup(ticker_html[n])
    return render_template(right_file, async_mode=socketio.async_mode, position=-1670, tickers=TICKERS, html=ticker_html)


@socketio.on('connect', namespace='/graphSock')
def connect():
    global update_feeds
    if update_feeds is None:
        update_feeds = socketio.start_background_task(target=update_thread, tickers=len(RSS))
    sleep(2)
    socketio.emit('restart', {'tickers': TICKERS}, namespace='/graphSock')

if __name__ == '__main__':
    print('getting news feeds...')
    for i in range(0, len(RSS)):
        ticker_html[i] = get_news_html(RSS[i])
    print('starting app')
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True)