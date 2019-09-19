from flask import Flask, render_template, Markup
from flask_socketio import SocketIO
import sqlite3
import tweepy
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from watson_developer_cloud import NaturalLanguageUnderstandingV1, watson_service
from watson_developer_cloud.natural_language_understanding_v1 \
    import Features, EmotionOptions
import googlemaps
from time import sleep, mktime, time
from queue import Queue
from threading import Thread, enumerate
from datetime import datetime, timedelta
from piNewsServer import get_list_html, get_news_html
from newsapi import NewsApiClient
from PricingModelServer import calc_price, gen_data
import quandl
import os
import traceback

naturalLanguageUnderstanding = NaturalLanguageUnderstandingV1(
    version='2018-11-16',
    iam_apikey='krKRo9lq4F4FdOaofZPABU8g34-hJWjNsqj-GZ4jEf2b',
    url='https://gateway-lon.watsonplatform.net/natural-language-understanding/api')

analyser = SentimentIntensityAnalyzer()

# Twitter Auth
consumer_key = "h9gQLi0ynR8I5Y3kD2yLzlSxT"
consumer_secret = "ACqR4JLtv7s7iuDRXnoXTUQ7NFLFnXKPNOa48UkFwU8cVSW8fH"
access_token = "484955690-V44erbnboNjEooWwYSuv5w10OcLE674EbejWf5Qv"
access_token_secret = "pIDcnNV9QPP26U9rvWqlj2P4CwwGq94470bcPQQDHR1MV"
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

gmaps = googlemaps.Client(key='AIzaSyBGkdrXQk7892-QEoWyzSND0m5CLSKKJZI')

app = Flask(__name__)
app.secret_key = b')\x9c\xc7\xa7\xb3\xd2\xa9\x8ch\xd6\xc9\xfc\xe6g!c'
socketio = SocketIO(app, async_mode='eventlet')
keywords = ["BPA", "bisphenol"]

con = sqlite3.connect('db/graphs_db.db')
cursor = con.cursor()

update_vals = None
tweet_queue = Queue()
emit_queue = Queue()
news_api = NewsApiClient(api_key='9603da2bf448477abdb31f47d4e4079e')
updated = time()
update_feeds = None
ticker_html = ""
news_list = []
EMOTIONS =['JOY','ANGER','DISGUST','SADNESS','FEAR']

pricing_models = {}
pricing_queue = Queue()

class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        # print(json.dumps(status._json, indent=2))
        print("%s - %s" % (status.text, status.user.location))
        cleaned_tweet = clean_tweet(status.text)
        cur_date = status.created_at
        sentiment_score = (sentiment(cleaned_tweet))
        emotion_scores = emotion(cleaned_tweet)
        if emotion_scores is not None:
            geo = {'lat': None, 'lng':None}
            if status.user.location != '':
                try:
                    geocode_result = gmaps.geocode(status.user.location)
                    if len(geocode_result) > 0 and 'geometry' in geocode_result[0].keys():
                        geo = geocode_result[0]['geometry']['location']
                except googlemaps.exceptions.HTTPError as e:
                    print(e)
            print("geo = %s" % geo)
            temp_con = sqlite3.connect('db/graphs_db.db')
            temp_cursor = temp_con.cursor()
            temp_cursor.execute('''INSERT INTO twitter(date, hour, minute, tweet, sentiment, joy, anger, disgust, sadness, fear, lat, lng)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (cur_date.strftime("%d/%m/%Y"),
                                                               cur_date.hour,
                                                               cur_date.minute,
                                                               cleaned_tweet,
                                                               sentiment_score,
                                                               emotion_scores['joy'],
                                                               emotion_scores['anger'],
                                                               emotion_scores['disgust'],
                                                               emotion_scores['sadness'],
                                                               emotion_scores['fear'],
                                                               geo['lat'],
                                                               geo['lng']))
            temp_con.commit()
            temp_cursor.execute('SELECT max(id) FROM twitter')
            new_id = temp_cursor.fetchone()[0]
            temp_con.close()
            print("adding data to queue")
            global tweet_queue
            tweet_queue.put({'date': cur_date.strftime("%d/%m/%Y"),
                             'hour': cur_date.hour,
                             'minute': cur_date.minute,
                            'tweet': cleaned_tweet,
                            'sentiment': sentiment_score,
                            'joy': emotion_scores['joy'],
                            'anger': emotion_scores['anger'],
                            'disgust': emotion_scores['disgust'],
                            'sadness': emotion_scores['sadness'],
                            'fear': emotion_scores['fear'],
                            'geo': geo,
                             'id': new_id
                             })


def clean_tweet(tweet):
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) | (\w +:\ / \ / \S +)", " ", tweet).split())


def sentiment(tweet):
    # print(tweet)
    analysis = analyser.polarity_scores(tweet)
    # print("vader: %s\n" % (analysis['compound']))
    return analysis['compound']

def emotion(tweet):
    try:
        response = naturalLanguageUnderstanding.analyze(
            text=tweet,
            features=Features(emotion=EmotionOptions(document=True))).get_result()
        emotions = response['emotion']['document']['emotion']
        return emotions
    except watson_service.WatsonApiException as e:
        print(e)
        return None

def gen_tweet_line(item):
    new_line = '<li class="news-list-item row-max {colour}"> \
				<span class="align-centre emotion col-xs-1">{emotion}</span> \
				<span class="align-centre score span col-xs-1">{score}</span> \
				<span class=" news-headline col-xs-8">{headline}</span> \
				<span class="align-centre time col-xs-1">{time}</span> \
			    </li>'.format(colour=item[4], emotion=item[0], score=item[1], headline=item[2], time=item[3])
    return Markup(new_line)


def gen_news_line(item):
    if item[0] >= 0:
        arrow_line = '<span class="list-item-up-icon"> </span>'
    else:
        arrow_line = '<span class="list-item-down-icon"> </span>'
    new_line = '<li class="list-item row-max up">\
				<span class="align-centre score col-xs-1">{sentiment}</span>\
				<span class="align-centre icon">{arrow}</span>\
				<span class="align-centre source">{source}</span>\
				<span class="list-item-content">{content}</span>\
				<span class="align-centre time">{time}</span>\
			    </li>'.format(sentiment=item[0], arrow=arrow_line, source=item[1], content=item[2], time=item[3])
    return Markup(new_line)


def twitter_thread():
    print("Starting twitter stream")
    myStreamListener = MyStreamListener()
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
    while True:
        try:
            myStream.filter(track=keywords)
        except Exception as e:
            print(e)
            sleep(1)


def data_update_thread():
    global bar_data, tweet_queue
    candle_hour = datetime.now().hour
    while True:
        if not tweet_queue.empty():
            print("***New Tweet Data***")
            new_tweet = tweet_queue.get()
            new_geo = new_tweet['geo']
            new_sentiment = new_tweet['sentiment']
            # Tweet List
            new_tweet_line = get_list_html([[
                new_tweet['tweet'],
                new_tweet['joy'],
                new_tweet['anger'],
                new_tweet['disgust'],
                new_tweet['sadness'],
                new_tweet['fear'],
                new_tweet['hour'],
                new_tweet['minute'],
                new_tweet['sentiment']
            ]])
            emit_queue.put(['update-tweets', {'tweet_html': gen_tweet_line(new_tweet_line[0])}, '/graphSock'])
            #  Scatter
            # pricing_queue.put([new_tweet['date'], new_tweet['sentiment'], new_tweet['id']])
            #  Heatmap
            if new_geo['lat'] is not None and new_sentiment < 0:
                emit_queue.put(['update-heatmap', new_geo, '/graphSock'])
            bar_data.append([None, new_tweet['joy'], new_tweet['anger'], new_tweet['disgust'],
                                    new_tweet['sadness'], new_tweet['fear']])
            # vr
            emit_queue.put(['update-vr-tweet',
                          {'tweet': new_tweet['tweet'],
                           'sentiment': new_tweet['sentiment'],
                           'joy': new_tweet['joy'],
                           'anger': new_tweet['anger'],
                           'disgust': new_tweet['disgust'],
                           'sadness': new_tweet['sadness'],
                           'fear': new_tweet['fear']}, '/graphSock'])
            #  Candle
            if new_tweet['hour'] != candle_hour:
                new_candle_data = update_candle()
                # emit_queue.put(['update-candle', {'data':new_candle_data}, '/graphSock'])
                candle_hour = new_tweet['hour']
            # Rolling News
                new_results = news_api.get_everything(q='bisphenol', sort_by='relevancy', page_size=100, language='en')
                new_articles = []
                new_list_articles = []
                for new_article in new_results['articles']:
                    new_articles.append([new_article['source']['name'], new_article['title'], new_article['publishedAt']])
                    new_date = new_article['publishedAt'].split('T')[0]
                    new_date = new_date[2:].replace('-', '.')
                    new_list_articles.append(
                        gen_news_line([sentiment(new_article['title']), new_article['source']['name'], new_article['title'], new_date]))
                new_html = get_news_html(articles)
                if new_html is not None:
                    emit_queue.put(['update', {'ticker': 0, 'html': new_html}, '/graphSock'])
                # emit_queue.put(['update-news-list', {'html-arr': new_list_articles}, '/graphSock'])
        else:
            sleep(0.5)

def bar_update_thread():
    while True:
        for data in bar_data:
            emit_queue.put(['update-bar',
                          {'joy': data[1],
                             'anger': data[2],
                             'disgust': data[3],
                             'sadness': data[4],
                             'fear': data[5]},'/graphSock'])
            emit_queue.put(['change', {'all': True}, '/graphSock'])
            sleep(2)

def vr_update_thread(news):
    while True:
        for news_article in news:
            if len(news_article[2]) > 240:
                headline = news_article[2][0:240]
            else:
                headline = news_article[2]
            emit_queue.put(['update-vr-news',
                          {'news': headline,
                           'sentiment': news_article[0]},'/graphSock'])
            sleep(1)

def prices_update_thread():
    ftse_data = None
    ftse_update = time()
    while True:
        tweet_obj = pricing_queue.get()
        if ftse_data is None or time() - ftse_update > 3600:
            now = datetime.today()
            if now.weekday() > 5:
                days_prev = now.weekday() - 5 + 1
            else:
                days_prev = 1
            start_date = "%s-%s-%s" % (now.year, now.month, now.day - days_prev)
            end_date = "%s-%s-%s" % (now.year, now.month, now.day)
            ftse_data = quandl.get("CHRIS/LIFFE_Z1", authtoken="NP-HERKjNAxszM1r66X6",
                                   start_date=start_date, end_date=end_date)
            ftse_update = time()
        u_con = sqlite3.connect('db/graphs_db.db')
        u_cursor = u_con.cursor()
        try:
            d, m, y = tweet_obj[0].split('/')
            ftse = ftse_data.loc["%s-%s-%s" % (y, m, int(d) - 1)]
            u_cursor.execute('''INSERT into prices(id, sentiment) VALUES (?,?)''',
                             (tweet_obj[2], tweet_obj[1]))
            u_con.commit()
            for company in pricing_models:
                u_con = sqlite3.connect('db/graphs_db.db')
                u_cursor = u_con.cursor()
                u_cursor.execute(
                    '''UPDATE prices SET "{company}" = ? WHERE id = ?'''.format(**{"company": company.replace(' ', '')}),
                    (
                        calc_price(pricing_models, company, ftse.Settle, tweet_obj[1]),
                        tweet_obj[2]
                    ))
                u_con.commit()
        except Exception as e:
            # u_cursor.execute('''DELETE from prices WHERE id = ?''', (tweet_obj[2]))
            # u_con.commit()
            print("Price Update Error: %s" % e )
            traceback.print_exc()

def scatter_update_thread():
    while True:
        for company in pricing_models:
            u_con = sqlite3.connect('db/graphs_db.db')
            u_cursor = u_con.cursor()
            u_cursor.execute('''SELECT min("{0}"), max("{0}") FROM prices'''
                             .format(company.replace(' ', '')))
            min_max = u_cursor.fetchall()
            min_max = min_max[0]
            u_cursor.execute('''SELECT "{company}", sentiment, date_time
                                    FROM prices'''.format(**{"company": company.replace(' ', '')}))
            company_data = u_cursor.fetchall()
            company_data.reverse()
            company_data = company_data[0:100]
            happy = []
            sad = []
            for i in range(len(company_data)):
                try:
                    if company_data[i][1] >= 0:
                        happy.append([float(company_data[i][2]), float(company_data[i][0])])
                    else:
                        sad.append([float(company_data[i][2]), float(company_data[i][0])])
                except TypeError as e:
                    print(e)
                    pass
                emit_queue.put(['update-scatter', {'happy': happy, 'sad': sad, 'min_max':min_max}, '/graphSock'])
                sleep(10)


def update_candle():
    candle_con = sqlite3.connect('db/graphs_db.db')
    cursor = candle_con.cursor()
    new_candle_data = []
    cursor.execute('''SELECT date,
                             hour,
                             MAX(fear),
                             MIN(fear)
                        FROM twitter
                        GROUP BY date,
                             hour''')
    new_cursor = candle_con.cursor()
    now = 0
    cursor_data = cursor.fetchall()
    cursor_data.reverse()
    for row in cursor_data:
        now -= 1
        timestamp = now
        new_cursor.execute('''SELECT fear
                            FROM twitter
                            WHERE date=? AND hour=?''', (row[0], row[1]))
        sentiments = new_cursor.fetchall()
        opening = sentiments[0][0]
        closing = sentiments[-1][0]
        high = row[2]
        low = row[3]
        new_candle_data.append([int(timestamp), [opening, high, low, closing]])
    # new_candle_data.reverse()
    new_candle_data = new_candle_data[-48:]
    return new_candle_data


def update_thread():
    while True:
        if not emit_queue.empty():
            new_cmd = emit_queue.get()
            # if new_cmd[0] == 'update-scatter':
            socketio.emit(new_cmd[0], new_cmd[1], namespace=new_cmd[2])
            print("sent data to %s" % new_cmd[0])
        else:
            socketio.sleep(0.5)


@socketio.on('connect', namespace='/graphSock')
def connect():
    global update_vals
    if update_vals is None:
        get_tweets = Thread(target=twitter_thread, name='twitter')
        data_update = Thread(target=data_update_thread, name='data')
        update_bar = Thread(target=bar_update_thread, name='bar')
        update_scatter = Thread(target=scatter_update_thread, name='scatter')
        update_prices = Thread(target=prices_update_thread, name='prices')
        update_vr = Thread(target=vr_update_thread, args=[list_articles], name='vr')
        get_tweets.start()
        data_update.start()
        update_bar.start()
        update_scatter.start()
        update_prices.start()
        update_vr.start()
        print(enumerate())
        update_vals = socketio.start_background_task(target=update_thread)
    sleep(2)
    emit_queue.put(['restart', {'tickers': 1}, '/graphSock'])
    emit_queue.put(['update-vr-tweet',
                  {'tweet': 'BPA H@ppy',
                   'sentiment': 0.0,
                   'joy': 0.0,
                   'anger': 0.0,
                   'disgust': 0.0,
                   'sadness': 0.0,
                   'fear': 0.0 }, '/graphSock'])
    emit_queue.put(['update-vr-news',
                  {'news': "THE 10 SURPRISING THINGS YOU CAN'T RECYCLE",
                   'sentiment': 0.0},'/graphSock'])
    return


@socketio.on('bg_change')
def bg_event(bg_data):
    print(bg_data)
    screens = bg_data['screens']
    bg_num = bg_data['bg_num']
    bg_screens = []
    for i in range(len(screens)):
        if not os.path.exists('static/images/B%s_%s.jpg' % (bg_num, screens[i])):
            print('static/images/B%s_%s.jpg does not exist' % (bg_num, screens[i]))
        else:
            bg_screens.append(screens[i])
    emit_queue.put(['update-bg', {'bg': bg_num, 'screens': bg_screens}, '/graphSock'])


@app.route('/heatmap')
def heatmap():
    heatmap_file = 'heatmap.html'
    return render_template(heatmap_file, async_mode=socketio.async_mode,
                           initial_data=heatmap_data)

@app.route('/bar')
def bar():
    candle_file = 'bar.html'
    return render_template(candle_file, async_mode=socketio.async_mode,
                           initial_data=bar_data[0])

@app.route('/candle')
def candle():
    candle_file = 'candle.html'
    return render_template(candle_file, async_mode=socketio.async_mode,
                           sentiment_list=candle_data)

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
                           position=-1920 - 60, tickers=1, html=mu_ticker_html, news_list=news_list)

@app.route('/list_top')
def news_top():
    tweet_file = 'list.html'
    return render_template(tweet_file, async_mode=socketio.async_mode,
                           position=0, initial_data=list_articles)

@app.route('/list_bottom')
def news_bottom():
    tweet_file = 'list.html'
    return render_template(tweet_file, async_mode=socketio.async_mode,
                           position=1, initial_data=list_articles)

@app.route('/scatter')
def scatter():
    scatter_file = 'scatter.html'
    return render_template(scatter_file, async_mode=socketio.async_mode, initial_data=[],
                        price_data=price_data)

@app.route('/vr')
def vr():
    vr_file = 'vr.html'
    return render_template(vr_file, async_mode=socketio.async_mode )

if __name__ == '__main__':
    print('getting data...')
    results = news_api.get_everything(q='bisphenol', sort_by='relevancy', page_size=100, language='en')
    articles = []
    list_articles = []
    for article in results['articles']:
        articles.append([article['source']['name'], article['title'], article['publishedAt']])
        date = article['publishedAt'].split('T')[0]
        date = date[2:].replace('-', '.')
        list_articles.append([sentiment(article['title']), article['source']['name'], article['title'], date])
    con = sqlite3.connect('db/graphs_db.db')
    cursor = con.cursor()

    cursor.execute('''SELECT sentiment,
                            lat,
                            lng
                        FROM twitter
                        WHERE lat NOTNULL
                        AND sentiment < 0''')

    heatmap_data = cursor.fetchall()

    cursor = con.cursor()
    cursor.execute('''SELECT tweet,
                                 joy,
                                 anger,
                                 disgust,
                                 sadness,
                                 fear
                            FROM twitter''')

    bar_data = cursor.fetchall()

    candle_data = update_candle()

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

    ticker_html = get_news_html(articles)
    news_list = get_list_html(cursor.fetchall())

    cursor.execute('''SELECT *
                            FROM price_model_data''')

    all_data = cursor.fetchall()
    cursor.execute('''SELECT * FROM prices ORDER BY id DESC LIMIT 1; ''')
    latest_price = cursor.fetchall()[0]
    price_data = []
    for i in range(len(all_data)):
        data = all_data[i]
        pricing_models[data[0]] = {"mod": data[1], "hdd": data[2], "ftse": data[3], "bpa": data[4]}
        try:
            price_data.append([data[0][0:20], "£%.2f" % float(latest_price[i + 2])])
        except Exception:
            pass


    print('starting app')
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True)