from flask import Flask, render_template, Markup
from flask_socketio import SocketIO
from time import sleep, time
from newsapi import NewsApiClient
import sqlite3

app = Flask(__name__)
app.secret_key = b')\x9c\xc7\xa7\xb3\xd2\xa9\x8ch\xd6\xc9\xfc\xe6g!c'
socketio = SocketIO(app, async_mode='eventlet')

api = NewsApiClient(api_key='9603da2bf448477abdb31f47d4e4079e')
results = api.get_everything(q='bisphenol', sort_by='relevancy', page_size=100, language='en')
articles = []
for article in results['articles']:
    articles.append([article['source']['name'], article['title'], article['publishedAt']])
updated = time()
update_feeds = None
ticker_html = ""
news_list = []
EMOTIONS =['JOY','ANGER','DISGUST','SADNESS','FEAR']

def get_news_html():
    html_content = ""
    for article in articles:
        html_content += '<div class="news-ticker-item ti_news"><span class="ticker-up-icon"> </span><span class="news-ticker-item-text"> %s </span></div>\n' % article[1].replace(' ', '&nbsp;')
    # print(html_content)
    return html_content


def get_list_html(tweets):
    list_html = []
    for tweet in tweets:
        emotions = [ abs(tweet[1]), abs(tweet[2]), abs(tweet[3]), abs(tweet[4]), abs(tweet[5])]
        max_val = emotions.index(max(emotions))
        value = tweet[max_val + 1]
        if tweet[8] > 0:
            colour = 'green'
        else:
            colour = 'red'
        list_html.append([Markup(EMOTIONS[max_val]),
                          Markup(value),
                          Markup(tweet[0]),
                          Markup("%s:%s GMT" % (tweet[6], tweet[7])),
                          Markup(colour)
                          ])
    #print(list_html)
    return list_html


def update_thread(tickers):
    global ticker_html, news_list, updated, articles
    socketio.sleep(3)
    while True:
        if time() - updated > 3600:
            print("updating feeds")
            new_results = api.get_everything(q='bisphenol', sort_by='relevancy', page_size=100, language='en')
            articles = []
            for article in new_results['articles']:
                articles.append([article['source']['name'], article['title'], article['publishedAt']])
            updated = time()
        for i in range(0, tickers):
            ticker = i
            new_html = get_news_html()
            if new_html is not None:
                ticker_html = new_html
                socketio.emit('update', {'ticker':ticker, 'html': new_html}, namespace='/graphSock')
        # news_list = get_list_html()
        socketio.sleep(1800)



@app.route('/news_left')
def left():
    left_file = 'news.html'
    mu_ticker_html = Markup(ticker_html)
    return render_template(left_file, async_mode=socketio.async_mode,
                           position=0, tickers=1, html=mu_ticker_html, news_list=news_list)


@app.route('/news_right')
def right():
    right_file = 'news.html'
    mu_ticker_html = Markup(ticker_html)
    return render_template(right_file, async_mode=socketio.async_mode,
                           position=-1680 - 60, tickers=1, html=mu_ticker_html, news_list=news_list)


@socketio.on('connect', namespace='/graphSock')
def connect():
    global update_feeds
    if update_feeds is None:
        update_feeds = socketio.start_background_task(target=update_thread, tickers=1)
    sleep(2)
    socketio.emit('restart', {'tickers': 1}, namespace='/graphSock')

if __name__ == '__main__':
    print('getting news feeds...')
    con = sqlite3.connect('db/graphs_db.db')
    cursor = con.cursor()

    cursor.execute('''SELECT tweet,
                             joy,
                             anger,
                             disgust,
                             sadness,
                             fear,
                             hour,
                             minute,
                             sentiment
                        FROM twitter''')

    all_data = cursor.fetchall()
    ticker_html = get_news_html()
    news_list = get_list_html(all_data)
    print('starting app')
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True)