from flask import Flask, render_template, Markup, flash
from flask_socketio import SocketIO
from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)
app.secret_key = b')\x9c\xc7\xa7\xb3\xd2\xa9\x8ch\xd6\xc9\xfc\xe6g!c'
socketio = SocketIO(app, async_mode='eventlet')
update_vals = None
DATA_WAIT = 2
api = NewsApiClient(api_key='9603da2bf448477abdb31f47d4e4079e')
articles = []
analyser = SentimentIntensityAnalyzer()

def sentiment(tweet):
    # print(tweet)
    analysis = analyser.polarity_scores(tweet)
    # print("vader: %s\n" % (analysis['compound']))
    return analysis['compound']

def update_thread():
    while True:
        socketio.emit('update-tweets', {}, namespace='/graphSock')
        socketio.sleep(DATA_WAIT)

@socketio.on('connect', namespace='/graphSock')
def connect():
    global update_vals
    # if update_vals is None:
    #     update_vals = socketio.start_background_task(target=update_thread)

@app.route('/list_top')
def news_list():
    tweet_file = 'list.html'
    return render_template(tweet_file, async_mode=socketio.async_mode,
                           initial_data=articles)

if __name__ == '__main__':
    print('getting data...')
    results = api.get_everything(q='bisphenol', sort_by='relevancy', page_size=100, language='en')
    for article in results['articles']:
        date = article['publishedAt'].split('T')[0]
        date = date[2:].replace('-', '.')
        articles.append([sentiment(article['title']), article['source']['name'], article['title'], date])
    print('starting app')
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True)