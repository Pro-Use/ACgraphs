import quandl
from flask import Flask, render_template, Markup, flash
from flask_socketio import SocketIO
import sqlite3
from time import time
from datetime import datetime


app = Flask(__name__)
app.secret_key = b')\x9c\xc7\xa7\xb3\xd2\xa9\x8ch\xd6\xc9\xfc\xe6g!c'
socketio = SocketIO(app, async_mode='eventlet')
update_vals = None
pricing_models = {}
ftse_data = None
ftse_update = time() - 3601

def update_thread():
    while True:
        now = datetime.today()
        for company in pricing_models:
            u_con = sqlite3.connect('db/graphs_db.db')
            u_cursor = u_con.cursor()
            u_cursor.execute('''SELECT "{company}", sentiment
                                    FROM prices'''.format(**{"company": company.replace(' ', '')}))
            company_data = u_cursor.fetchall()
            try:
                for i in range(len(company_data)):
                    print(company_data[i])
                    company_data[i] = [float(company_data[i][0]), company_data[i][1]]
                socketio.emit('update-scatter',
                              {'data': company_data}, namespace='/graphSock')
                socketio.sleep(5)
            except TypeError:
                pass

def calc_price(company,ftse,bpa,hdd=0):
    f = ftse * pricing_models[company]['ftse']
    h = hdd * pricing_models[company]['hdd']
    b = bpa * pricing_models[company]['bpa']
    return pricing_models[company]['mod'] + f + h + b

def gen_data(now, company):
    global ftse_data, ftse_update
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
        # print(ftse_data)
    company_data = []
    vals = []
    if now.weekday() > 5:
        days_prev = now.weekday() - 5 + 1
    else:
        days_prev = 1
    ftse = ftse_data.loc["%s-%s-%s" % (now.year, now.month, now.day - days_prev)]
    for s in range(0, 10):
        sent = s / 10
        new_val = calc_price(company, ftse.Settle, sent)
        vals.append(new_val)
        company_data.append([new_val, sent])
    return company_data, max(vals), min(vals)

def insert_tweet_data(tweet_obj):
    d, m, y = tweet_obj[0].split('/')
    global ftse_data, ftse_update
    if ftse_data is None or time() - ftse_update > 3600:
        start_date = "%s-%s-%s" % (y, m, int(d) - 1)
        end_date = "%s-%s-%s" % (y, m, d)
        ftse_data = quandl.get("CHRIS/LIFFE_Z1", authtoken="NP-HERKjNAxszM1r66X6",
                               start_date=start_date, end_date=end_date)
        ftse_update = time()
    u_con = sqlite3.connect('db/graphs_db.db')
    u_cursor = u_con.cursor()
    u_cursor.execute('''INSERT into prices(id, sentiment) VALUES (?,?)''',
                   (tweet_obj[2], tweet_obj[1]))
    u_con.commit()
    ftse = ftse_data.loc["%s-%s-%s" % (y, m, d)]
    for company in pricing_models:
        print('''UPDATE prices SET %s = %s WHERE id = %s''' %
              (company.replace(' ', ''),
               calc_price(company, ftse.Settle, tweet_obj[1]),
               tweet_obj[2]
               ))

        u_con = sqlite3.connect('db/graphs_db.db')
        u_cursor = u_con.cursor()
        u_cursor.execute(
            '''UPDATE prices SET "{company}" = ? WHERE id = ?'''.format(**{"company": company.replace(' ', '')}),
            (
                calc_price(company, ftse.Settle, tweet_obj[1]),
                tweet_obj[2]
            ))
        u_con.commit()

def update_db():
    u_con = sqlite3.connect('db/graphs_db.db')
    u_cursor = u_con.cursor()
    u_cursor.execute('''SELECT date,
                            sentiment,
                            id
                        FROM twitter''')

    tweet_data = u_cursor.fetchall()
    d,m,y = tweet_data[0][0].split('/')
    start_date = "%s-%s-%s" % (y, m, d)
    d, m, y = tweet_data[-1][0].split('/')
    end_date = "%s-%s-%s" % (y, m, d)
    global ftse_data, ftse_update
    ftse_data =  quandl.get("CHRIS/LIFFE_Z1", authtoken="NP-HERKjNAxszM1r66X6",
                            start_date=start_date, end_date=end_date )
    ftse_update = time()
    for tweet in tweet_data:
        insert_tweet_data(tweet)

@socketio.on('connect', namespace='/graphSock')
def connect():
    global update_vals
    if update_vals is None:
        update_vals = socketio.start_background_task(target=update_thread)

@app.route('/scatter')
def scatter():
    scatter_file = 'scatter.html'
    return render_template(scatter_file, async_mode=socketio.async_mode, initial_data=initial_data,
                           max=first_max, min=first_min, price_data=price_data)

if __name__ == '__main__':
    print('getting data...')
    con = sqlite3.connect('db/graphs_db.db')
    cursor = con.cursor()

    cursor.execute('''SELECT *
                        FROM price_model_data''')

    all_data = cursor.fetchall()
    cursor.execute('''SELECT * FROM prices ORDER BY id DESC LIMIT 1; ''')
    latest_price = cursor.fetchall()[0]
    price_data = []
    for i in range(len(all_data)):
        data = all_data[i]
        pricing_models[data[0]] = {"mod": data[1],"hdd": data[2],"ftse": data[3],"bpa": data[4]}
        price_data.append([data[0][0:20], "£%.2f" % float(latest_price[i + 2])])
    print(price_data)
    initial_data = None
    for company in pricing_models.keys():
        initial_data, first_max, first_min = gen_data(datetime.today(), company)
        break
    print(initial_data, first_max, first_min)
    print('starting app')
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True)

