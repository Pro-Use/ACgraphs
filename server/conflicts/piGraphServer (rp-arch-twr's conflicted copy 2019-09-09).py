from flask import Flask, render_template
from flask_socketio import SocketIO
import sqlite3
import tweepy
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from watson_developer_cloud import NaturalLanguageUnderstandingV1, watson_service
from watson_developer_cloud.natural_language_understanding_v1 \
    import Features, EmotionOptions, SentimentOptions
import googlemaps
from time import sleep, mktime
from queue import Queue
from threading import Thread
from datetime import datetime, timedelta

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
            temp_con.close()
            print("adding data to queue")
            tweet_queue.put({'date': cur_date.strftime("%d/%m/%Y"),
                            'tweet': cleaned_tweet,
                            'sentiment': sentiment_score,
                            'joy': emotion_scores['joy'],
                            'anger': emotion_scores['anger'],
                            'disgust': emotion_scores['disgust'],
                            'sadness': emotion_scores['sadness'],
                            'fear': emotion_scores['fear'],
                            'geo': geo
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
    while True:
        if not tweet_queue.empty():
            new_tweet = tweet_queue.get()
            new_geo = new_tweet['geo']
            new_sentiment = new_tweet['sentiment']
            if new_geo['lat'] is not None and new_sentiment < 0:
                emit_queue.put(['update-heatmap', new_geo, '/graphSock'])
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
            sleep(2)

@socketio.on('connect', namespace='/graphSock')
def connect():
    global update_vals
    if update_vals is None:
        get_tweets = Thread(target=twitter_thread)
        get_tweets.start()
        update_vals = socketio.start_background_task(target=update_thread)
    return

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

if __name__ == '__main__':
    print('getting data...')
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

    cursor = con.cursor()
    candle_data = []
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
        candle_data.append([int(timestamp), [opening, high, low, closing]])


    print('starting app')
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True)