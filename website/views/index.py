import os
import re
import flask
import shutil
import hashlib
import website
import datetime
import datedelta
from string import Template
from random import randrange
from flask import url_for, render_template_string, jsonify, flash
from website.model import get_db
from yahoo_fin.stock_info import *
from yahoo_fin import news
import numpy as np
import pandas as pd
import json
import plotly
import plotly.express as px

'''
RECALL

- GET  : Used to request data from a specified resource.
- POST : Used to send data to a server to create/update a resource. 

'''

data = None

@website.app.route('/')
def landing_page():
    '''Display landing page of your site.'''
    wallpaper = 'images/warren0.jpeg'
    images = flask.url_for('static', filename=wallpaper)
    return flask.render_template("landing_page.html", images=images)

@website.app.route('/invest/')
def invest_page():
    '''Display landing page of your site.'''
    wallpaper = 'images/invest.jpeg'
    images = flask.url_for('static', filename=wallpaper)
    return flask.render_template("landing_page.html", images=images)


@website.app.route('/accounts/logout/')
def logout_page():
    """Logout page."""
    flask.session.clear()
    return flask.redirect(flask.url_for('landing_page'))

@website.app.route('/philosophy/', methods=['POST', 'GET'])
def philosophy_page():
    images = flask.url_for('static', filename='images/warren2.gif')
    return flask.render_template("philosophy_page.html", images=images)

@website.app.route('/accounts/login/', methods=['GET', 'POST'])
def login_page():
    """Login page for project."""

    if flask.request.method == 'POST':
        get_user = get_db().cursor().execute(
            "SELECT DISTINCT * FROM users WHERE name = ?",
            [flask.request.form['username']]
            ).fetchone()

        if get_user is not None:
            if handle_password(flask.request.form['password']) == get_user['password']:
                flask.session['username'] = flask.request.form['username']
                flash('Welcome back!', "success")
                return flask.redirect(flask.url_for('history_page'))
            flash( "Incorrect Password - Please try again.", "danger")
            return flask.redirect(flask.url_for('login_page'))

    if check_usersession():
        flash('Welcome back!', "success")
        return flask.redirect(flask.url_for('history_page'))

    logo = flask.url_for('static', filename='images/logo.png')
    header = flask.url_for('static', filename='images/banner1.jpeg')
    images = flask.url_for('static', filename='images/warren.gif')
    return flask.render_template("login_page.html", logo=logo, header=header, images=images)

@website.app.route('/accounts/create/', methods=['GET', 'POST'])
def create_account():
    
    if flask.request.method == 'POST':
        username = flask.request.form['username']
        user_exists = get_db().cursor().execute(
            "SELECT COUNT(*) AS num FROM users WHERE name = ?", [username]
            ).fetchone()

        if user_exists['num'] != 0:
            flash('That username is taken. Try another.', "warning")
            return flask.redirect(url_for('create_account'))

        password = flask.request.form['password']
        if password == "" or password == username:
            flash('Please use a more secure password.', "warning")
            return flask.redirect(url_for('create_account'))

        email = flask.request.form['email']
        if not re.search(r"[\w\.-]+@[\w\.-]+(?:\.[\w]+)+", email):
            flash('Please use a true email address.', "warning")
            return flask.redirect(url_for('create_account'))

        age, exp = flask.request.form['age'], flask.request.form['exp']
        if age == ""  or not age.isdigit() or int(age) < 10:
            flash("Please make sure you're at least 10 years old to register an account.", "warning")
            return flask.redirect(url_for('create_account'))

        if exp == ""  or not exp.isdigit():
            flash("Please enter your years of experience.", "warning")
            return flask.redirect(url_for('create_account'))

        ct = datetime.datetime.now()
        hashed_p = handle_password(password)
        sql_string1 = '''INSERT INTO users(name, password, email, age, exp)
                        VALUES (?, ?, ?, ?, ?)'''
        get_db().cursor().execute(sql_string1, (username, hashed_p, email, int(age), int(exp)))
        flask.session['username'] = username

        sql_string2 = '''INSERT INTO users_finance(username, cash)
                        VALUES (?, ?)'''
        get_db().cursor().execute(sql_string2, (username, 1000.00))

        sql_string3 = '''INSERT INTO users_watchlist(username, ticker)
                        VALUES (?, ?)'''
        get_db().cursor().execute(sql_string3, (username, 'AAPL'))
        get_db().cursor().execute(sql_string3, (username, 'GOOG'))
        get_db().cursor().execute(sql_string3, (username, 'AMZN'))
        get_db().cursor().execute(sql_string3, (username, 'MSFT'))
        get_db().cursor().execute(sql_string3, (username, 'TSLA'))
        get_db().cursor().execute(sql_string3, (username, 'FB'))
        get_db().cursor().execute(sql_string3, (username, 'TWTR'))
        get_db().cursor().execute(sql_string3, (username, 'F'))

        flash('You have successfully create an account!', "success")
        return flask.redirect(flask.url_for('history_page'))

    if check_usersession():
        flash('You have successfully create an account!', "success")
        return flask.redirect(flask.url_for('history_page'))

    logo = flask.url_for('static', filename='images/logo.png')
    return flask.render_template("create_page.html", logo=logo)

@website.app.route('/history/', methods=['POST', 'GET'])
def history_page():
    '''Historical Data Page.'''
    if not check_usersession():
        flash("Please make sure you're login.", "warning")
        return flask.redirect(flask.url_for('login_page'))

    df = None
    global data
    if data is None:
        data = retrieve_data()

    # Get min & max dates.
    d1, d2 = min(data['dates']), max(data['dates'])
    d3 = max(data['dates'])

    data['price_diff'] = data['price_diff'].apply(lambda x: round(x, 2))
    data['percentage_diff'] = data['percentage_diff'].apply(lambda x: round(x, 2))
    data['price_color'] = data['price_diff'].apply(classify1)
    data['percent_color'] = data['percentage_diff'].apply(classify2)

    # Prepreocess dataset - get numbers.
    temp = data['status'].value_counts().sort_index(ascending=True).to_frame().reset_index()
    temp.columns = ['status', 'count']
    temp['status'] = temp['status'].replace({0: 'Loss', 1: 'Tie', 2: 'Gain'})

    v1 = int(temp[temp['status'] == 'Loss']['count'])
    v2 = int(temp[temp['status'] == 'Tie']['count'])
    v3 = int(temp[temp['status'] == 'Gain']['count'])

    df_01 = data.sort_values('price_diff', ascending=False)
    df_02 = data.sort_values('percentage_diff', ascending=False)

    a01 = df_01['tickers'][:50].tolist()[::-1]
    b01 = df_01['price_diff'][:50].tolist()[::-1]  
    d01 = len(b01)
    e01 = df_01['price_color'][:50].tolist()[::-1]

    a02 = df_02['tickers'][:50].tolist()[::-1]
    b02 = df_02['percentage_diff'][:50].tolist()[::-1]
    d02 = len(b02)
    e02 = df_02['percent_color'][:50].tolist()[::-1]

    if flask.request.method == 'POST':
        sd1 = flask.request.form["start_date"]
        sd2 = flask.request.form["end_date"]
        sd1 = max(d1, sd1) or d1
        sd2 = min(d2, sd2) or d2
        print(sd1, sd2)

        temp = data[(data['dates'] >= sd1) & (data['dates'] <= sd2)]
        df_01 = temp.sort_values('price_diff', ascending=False)
        df_02 = temp.sort_values('percentage_diff', ascending=False)

        temp = temp['status'].value_counts().sort_index(ascending=True).to_frame().reset_index()
        temp.columns = ['status', 'count']
        temp['status'] = temp['status'].replace({0: 'Loss', 1: 'Tie', 2: 'Gain'})
        v1 = int(temp[temp['status'] == 'Loss']['count'])
        v2 = int(temp[temp['status'] == 'Tie']['count'])
        v3 = int(temp[temp['status'] == 'Gain']['count'])
        print(v1, v2, v3)

        a01 = df_01['tickers'][:50].tolist()[::-1]
        b01 = df_01['price_diff'][:50].tolist()[::-1]
        d01 = len(b01)
        e01 = df_01['price_color'][:50].tolist()[::-1]
        
        a02 = df_02['tickers'][:50].tolist()[::-1]
        b02 = df_02['percentage_diff'][:50].tolist()[::-1]

        d02 = len(b02)
        e02 = df_02['percent_color'][:50].tolist()[::-1]

        return flask.render_template("history.html", md1 = str(sd1), md2 = str(sd2),\
               md3 = str(d3),v1=v1, v2=v2, v3=v3, a01=a01, b01=b01, d01=d01, e01=e01,\
               a02=a02, b02=b02, d02=d02, e02=e02)

    return flask.render_template("history.html", md1 = str(d1), md2 = str(d2),\
     md3 = str(d3), v1=v1, v2=v2, v3=v3, a01=a01, b01=b01, d01=d01, e01=e01,\
     a02=a02, b02=b02, d02=d02, e02=e02)

@website.app.route('/feedback/', methods=['POST', 'GET'])
def feedback_page():

    if not check_usersession():
        flash("Please make sure you're login.", "warning")
        return flask.redirect(flask.url_for('login_page'))

    username = flask.session['username']
    feedback_list = []
    likes_list = []

    main_list = get_db().cursor().execute(
        "SELECT DISTINCT ufid, title, comments FROM users_feedback").fetchall()

    temp_list = get_db().cursor().execute(
        "SELECT DISTINCT ufid, username FROM feedback_upvotes").fetchall()

    for t in temp_list:
        likes_list.append([t['ufid'], t['username']])

    for f in main_list:
        feedback_list.append([f['ufid'], f['title'], f['comments']])

    likes_df = pd.DataFrame(likes_list, columns=['id', 'username'])
    likes_df = likes_df.groupby(['id'])['username'].count().reset_index()

    feedback_df = pd.DataFrame(feedback_list, columns=['id', 'title', 'comment'])

    res = feedback_df.merge(likes_df, on='id', how='left')
    res['username'] = res['username'].fillna(0)
    res['username'] = res['username'].astype(int)
    print(res)
    final_df = res.sort_values(by=['username'], ascending=False)
    feedback_list = final_df.values.tolist()

    for l in feedback_list:
        print(l, "\n")

    if flask.request.method == 'POST' and "title" in flask.request.form:

        # insert into table (feature_id, username, title, comments)
        title = flask.request.form['title']
        comments = flask.request.form['comments']

        if len(title) == 0 or len(comments) == 0:
            flash("Please make sure you've filled in both title & suggestion sections!", "danger")
            return flask.redirect(flask.url_for('feedback_page'))
        
        insert_sql1 = '''INSERT INTO users_feedback(username, title, comments) VALUES (?, ?, ?)'''
        get_db().cursor().execute(insert_sql1, (username, title, comments))  
        return flask.redirect(flask.url_for('feedback_page'))     

    elif flask.request.method == 'POST' and "upvote" in flask.request.form:

        fid = flask.request.form['upvote']

        check = get_db().cursor().execute(
            "SELECT DISTINCT ufid, username FROM feedback_upvotes WHERE ufid = ? AND username = ?",
            [fid, username]).fetchone()

        if check is None:
            insert_sql = '''INSERT INTO feedback_upvotes(ufid, username) VALUES (?, ?)'''
            get_db().cursor().execute(insert_sql, (fid, username))

        return flask.redirect(flask.url_for('feedback_page'))


    return flask.render_template("feedback.html", feedback=feedback_list)


@website.app.route('/stock_pick_price/', methods=['POST', 'GET'])
def stock_pick_price():
    # 1. Get data - past 40 days.

    if not check_usersession():
        flash("Please make sure you're login.", "warning")
        return flask.redirect(flask.url_for('login_page'))

    username = flask.session['username']
    df = pd.read_csv('stock_rec.csv', index_col=0)
    # 2. Sort by price diff.
    df['price_color'] = df['price_diff'].apply(classify4)
    df = df.sort_values('price_diff', ascending=False)

    values = {}
    values[0] = '10'
    values[1] = '5'

    # 3. Declare global variables. 
    variables, ticker_list, user_info, stock_info  = {}, {}, {}, {}
    curr_ticker, ticker_date, ori_ticker = None, None, None
    start_date, end_date = datetime.date.today() - datetime.timedelta(days=365), datetime.date.today()

    # 0 - ticker list, 1 - price_diff list, 2 - price color list
    # 3 - length, 4 - boolean ($ / %)
    variables[0] = df['tickers'][:35].tolist()
    variables[1] = df['price_diff'][:35].tolist()[::-1]
    variables[2] = df['price_color'][:35].tolist()[::-1]
    variables[3] = len(variables[2])
    variables[4] = '$'

    for i in range(1, 36):
        ticker_list[i] = variables[0][i-1]
    variables[0] = variables[0][::-1]


    user_stats = get_db().cursor().\
                  execute("SELECT DISTINCT ticker, return, status FROM users_historical WHERE username = ?",\
                           [username]).fetchall()

    t, r, s = [], [], []
    for stats in user_stats:
        t.append(stats['ticker'])
        r.append(stats['return'])
        s.append(stats['status'])

    user_stat = pd.DataFrame({'ticker': t, 'return': r, 'status': s})

    user_stat0 = user_stat[user_stat['status'] == 0]
    user_stat1 = user_stat[user_stat['status'] == 1]
    user_stat2 = user_stat[user_stat['status'] == 2]


    select_sql = '''SELECT DISTINCT cash FROM users_finance WHERE username = ?'''
    user_info[1] = get_db().cursor().execute(select_sql, [username]).fetchone()['cash']
    user_info[2] = round(sum(user_stat['return']), 2)
    user_info[3] = user_stat2.shape[0]
    user_info[4] = user_stat1.shape[0]
    user_info[5] = user_stat0.shape[0]

    curr_ticker = ticker_list[1]
    ori_ticker = pd.DataFrame(get_data(curr_ticker, start_date=start_date, end_date=end_date)) 
    ori_ticker.reset_index(inplace=True)
    ori_ticker = ori_ticker.rename(columns = {'index': 'date'})
    ori_ticker['date'] = ori_ticker['date'].dt.strftime("%Y-%m-%d")

    ticker_date = get_db().cursor().\
                  execute("SELECT DISTINCT dates FROM historical_data WHERE tickers = ?",\
                           [curr_ticker]).fetchone()

    stock_info[0] = ori_ticker['date'].tolist()
    stock_info[1] = ori_ticker['open'].tolist()
    stock_info[2] = ori_ticker['high'].tolist()
    stock_info[3] = ori_ticker['low'].tolist()
    stock_info[4] = ori_ticker['close'].tolist() 


    if flask.request.method == 'POST' and "get_tickers" in flask.request.form:
        index = int(flask.request.form["get_tickers"])

        if curr_ticker != ticker_list[index]:
            curr_ticker = ticker_list[index]
            ori_ticker = pd.DataFrame(get_data(curr_ticker, start_date=start_date, end_date=end_date)) 
            ori_ticker.reset_index(inplace=True)
            ori_ticker = ori_ticker.rename(columns = {'index': 'date'}) 
            ticker_date = get_db().cursor().\
                  execute("SELECT DISTINCT dates FROM historical_data WHERE tickers = ?",\
                           [curr_ticker]).fetchone()
            ori_ticker['date'] = ori_ticker['date'].dt.strftime("%Y-%m-%d")
            stock_info[0] = ori_ticker['date'].tolist()
            stock_info[1] = ori_ticker['open'].tolist()
            stock_info[2] = ori_ticker['high'].tolist()
            stock_info[3] = ori_ticker['low'].tolist()
            stock_info[4] = ori_ticker['close'].tolist()
        
        return flask.render_template("stock_picks.html", v_01 = variables, v_02=ticker_list, v_03=user_info,\
                                      v_04 = stock_info, v_05=curr_ticker, v_06 = ticker_date['dates'], v_07=values)
    
    elif flask.request.method == 'POST' and "shares" in flask.request.form:
        
        print(flask.request.form)
        val1 = flask.request.form['tickers']
        val2 = int(flask.request.form["shares"])
        ticker_check = get_db().cursor().\
                  execute("SELECT DISTINCT ticker FROM users_current WHERE username = ?",\
                           [username]).fetchall()

        if len(ticker_check) >= 5:
            flash('Currently hold 5 stocks. Cannot execute this order!' , "danger")
            return flask.redirect(url_for('stock_pick_price'))

        cash = get_db().cursor().\
                  execute("SELECT cash FROM users_finance WHERE username = ?",\
                           [username]).fetchone()['cash']

        stock_price = round(float(get_live_price(val1)), 2)
        total_price = stock_price * val2
        if cash - total_price <= 1.00:
            flash('You do not have enough cash to execute this order!' , "danger")
            return flask.redirect(url_for('stock_pick_price')) 

        # update cash
        # users_current 
        remainding = round(cash - total_price, 2)
        update_sql = '''UPDATE users_finance SET cash = ? WHERE username = ?'''
        get_db().cursor().execute(update_sql, (remainding, username))


        insert_sql = '''INSERT INTO users_current(username, ticker, shares, cost) VALUES (?, ?, ?, ?)'''
        get_db().cursor().execute(insert_sql, (username, val1, val2, stock_price))

        flash('You have successfully purchased ' + str(val2) + ' shares of ' + val1 + '! You have $' + str(remainding) + ' in your account.', "success")
        return flask.redirect(url_for('stock_pick_price'))

    elif flask.request.method == 'POST' and "add_watchlist" in flask.request.form:
        print(flask.request.form)
        watchlist_ticker = flask.request.form['tickers']
        ticker_check = get_db().cursor().\
                  execute("SELECT DISTINCT ticker FROM users_watchlist WHERE username = ? AND ticker = ?",\
                           [username, watchlist_ticker]).fetchone()
        if ticker_check is None:
            insert_sql = '''INSERT INTO users_watchlist(username, ticker) VALUES (?, ?)'''
            get_db().cursor().execute(insert_sql, (username, watchlist_ticker))
            flash('You have successfully add ' + watchlist_ticker + ' to your watchlist!' , "success")
            return flask.redirect(url_for('stock_pick_price'))
        else:
            flash(watchlist_ticker + ' is already in your watchlist!' , "danger")
            return flask.redirect(url_for('stock_pick_price'))


    return flask.render_template("stock_picks.html", v_01 = variables, v_02=ticker_list, v_03=user_info,\
                                  v_04 = stock_info, v_05=curr_ticker, v_06 = ticker_date['dates'], v_07=values)

@website.app.route('/stock_pick_percentage/', methods=['POST', 'GET'])
def stock_pick_percentage():

    if not check_usersession():
        flash("Please make sure you're login.", "warning")
        return flask.redirect(flask.url_for('login_page'))

    # 1. Get data - past 40 days.
    #df = stock_recommendations()
    #df.to_csv('stock_rec.csv')
    username = flask.session['username']
    df = pd.read_csv('stock_rec.csv', index_col=0)

    values = {}
    values[0] = '50%'
    values[1] = '15%'

    # 2. Sort by price diff.
    df['percentage_color'] = df['percentage_diff'].apply(classify3)
    df = df.sort_values('percentage_diff', ascending=False)

    # 3. Declare global variables. 
    variables, ticker_list, user_info, stock_info  = {}, {}, {}, {}
    curr_ticker, ticker_date, ori_ticker = None, None, None
    start_date, end_date = datetime.date.today() - datetime.timedelta(days=365), datetime.date.today()

    # 0 - ticker list, 1 - price_diff list, 2 - price color list
    # 3 - length, 4 - boolean ($ / %)
    variables[0] = df['tickers'][:35].tolist()
    variables[1] = df['percentage_diff'][:35].tolist()[::-1]
    variables[2] = df['percentage_color'][:35].tolist()[::-1]
    variables[3] = len(variables[2])
    variables[4] = '%'

    for i in range(1, 36):
        ticker_list[i] = variables[0][i-1]
    variables[0] = variables[0][::-1]

    user_stats = get_db().cursor().\
                  execute("SELECT DISTINCT ticker, return, status FROM users_historical WHERE username = ?",\
                           [username]).fetchall()

    t, r, s = [], [], []
    for stats in user_stats:
        t.append(stats['ticker'])
        r.append(stats['return'])
        s.append(stats['status'])

    user_stat = pd.DataFrame({'ticker': t, 'return': r, 'status': s})

    user_stat0 = user_stat[user_stat['status'] == 0]
    user_stat1 = user_stat[user_stat['status'] == 1]
    user_stat2 = user_stat[user_stat['status'] == 2]


    select_sql = '''SELECT DISTINCT cash FROM users_finance WHERE username = ?'''
    user_info[1] = get_db().cursor().execute(select_sql, [username]).fetchone()['cash']
    user_info[2] = round(sum(user_stat['return']), 2)
    user_info[3] = user_stat2.shape[0]
    user_info[4] = user_stat1.shape[0]
    user_info[5] = user_stat0.shape[0]




    curr_ticker = ticker_list[1]
    ori_ticker = pd.DataFrame(get_data(curr_ticker, start_date=start_date, end_date=end_date)) 
    ori_ticker.reset_index(inplace=True)
    ori_ticker = ori_ticker.rename(columns = {'index': 'date'})
    ori_ticker['date'] = ori_ticker['date'].dt.strftime("%Y-%m-%d")

    ticker_date = get_db().cursor().\
                  execute("SELECT DISTINCT dates FROM historical_data WHERE tickers = ?",\
                           [curr_ticker]).fetchone()

    stock_info[0] = ori_ticker['date'].tolist()
    stock_info[1] = ori_ticker['open'].tolist()
    stock_info[2] = ori_ticker['high'].tolist()
    stock_info[3] = ori_ticker['low'].tolist()
    stock_info[4] = ori_ticker['close'].tolist() 


    if flask.request.method == 'POST' and "get_tickers" in flask.request.form:
        index = int(flask.request.form["get_tickers"])

        if curr_ticker != ticker_list[index]:
            curr_ticker = ticker_list[index]
            ori_ticker = pd.DataFrame(get_data(curr_ticker, start_date=start_date, end_date=end_date)) 
            ori_ticker.reset_index(inplace=True)
            ori_ticker = ori_ticker.rename(columns = {'index': 'date'}) 
            ticker_date = get_db().cursor().\
                  execute("SELECT DISTINCT dates FROM historical_data WHERE tickers = ?",\
                           [curr_ticker]).fetchone()
            ori_ticker['date'] = ori_ticker['date'].dt.strftime("%Y-%m-%d")
            stock_info[0] = ori_ticker['date'].tolist()
            stock_info[1] = ori_ticker['open'].tolist()
            stock_info[2] = ori_ticker['high'].tolist()
            stock_info[3] = ori_ticker['low'].tolist()
            stock_info[4] = ori_ticker['close'].tolist()
        
        return flask.render_template("stock_picks.html", v_01 = variables, v_02=ticker_list, v_03=user_info,\
                                      v_04 = stock_info, v_05=curr_ticker, v_06 = ticker_date['dates'], v_07=values)
    
    elif flask.request.method == 'POST' and "shares" in flask.request.form:
        
        print(flask.request.form)
        val1 = flask.request.form['tickers']
        val2 = int(flask.request.form["shares"])
        ticker_check = get_db().cursor().\
                  execute("SELECT DISTINCT ticker FROM users_current WHERE username = ?",\
                           [username]).fetchall()

        if len(ticker_check) >= 5:
            flash('Currently hold 5 stocks. Cannot execute this order!' , "danger")
            return flask.redirect(url_for('stock_pick_percentage'))

        cash = get_db().cursor().\
                  execute("SELECT cash FROM users_finance WHERE username = ?",\
                           [username]).fetchone()['cash']

        stock_price = round(float(get_live_price(val1)), 2)
        total_price = stock_price * val2
        if cash - total_price <= 1.00:
            flash('You do not have enough cash to execute this order!' , "danger")
            return flask.redirect(url_for('stock_pick_percentage')) 

        # update cash
        # users_current 
        remainding = round(cash - total_price, 2)
        update_sql = '''UPDATE users_finance SET cash = ? WHERE username = ?'''
        get_db().cursor().execute(update_sql, (remainding, username))


        insert_sql = '''INSERT INTO users_current(username, ticker, shares, cost) VALUES (?, ?, ?, ?)'''
        get_db().cursor().execute(insert_sql, (username, val1, val2, stock_price))

        flash('You have successfully purchased ' + str(val2) + ' shares of ' + val1 + '! You have $' + str(remainding) + ' in your account.', "success")
        return flask.redirect(url_for('stock_pick_percentage'))

    elif flask.request.method == 'POST' and "add_watchlist" in flask.request.form:
        print(flask.request.form)
        watchlist_ticker = flask.request.form['tickers']
        ticker_check = get_db().cursor().\
                  execute("SELECT DISTINCT ticker FROM users_watchlist WHERE username = ? AND ticker = ?",\
                           [username, watchlist_ticker]).fetchone()
        if ticker_check is None:
            insert_sql = '''INSERT INTO users_watchlist(username, ticker) VALUES (?, ?)'''
            get_db().cursor().execute(insert_sql, (username, watchlist_ticker))
            flash('You have successfully add ' + watchlist_ticker + ' to your watchlist!' , "success")
            return flask.redirect(url_for('stock_pick_percentage'))
        else:
            flash(watchlist_ticker + ' is already in your watchlist!' , "danger")
            return flask.redirect(url_for('stock_pick_percentage'))            


    return flask.render_template("stock_picks.html", v_01 = variables, v_02=ticker_list, v_03=user_info,\
                                  v_04 = stock_info, v_05=curr_ticker, v_06 = ticker_date['dates'], v_07=values)


@website.app.route('/portfolio/<curr_ticker>/', methods=['POST', 'GET'])
def main_page(curr_ticker):

    if not check_usersession():
        flash("Please make sure you're login.", "warning")
        return flask.redirect(flask.url_for('login_page'))

    '''
    Functions:

    1.  Get all stocks from watchlist 
        - Remove watchlist
        - Click on stocks on watchlist
    2.  Get all current purchased stocks
        - Sell stocks
    3.  Get all users stats: 
        - Historical purchase
        - Update users cash

    '''


    username = flask.session['username']
    watchlist = []
    temp_list = get_db().cursor().execute(
        "SELECT DISTINCT ticker FROM users_watchlist WHERE username = ?", [username]
        ).fetchall()
    for tick in temp_list:
        watchlist.append([tick['ticker'], round(float(get_live_price(tick['ticker'])), 2)])


    curr_ticker_info = {}

    if curr_ticker == "None":
        curr_ticker = watchlist[0][0]
    ori_ticker = pd.DataFrame(get_data(curr_ticker, start_date=datetime.date.today() - datetime.timedelta(days=365), end_date=datetime.date.today())) 
    ori_ticker.reset_index(inplace=True)
    ori_ticker = ori_ticker.rename(columns = {'index': 'date'}) 
    ori_ticker['date'] = ori_ticker['date'].dt.strftime("%Y-%m-%d")
    curr_ticker_info[0] = ori_ticker['date'].tolist()
    curr_ticker_info[1] = ori_ticker['open'].tolist()
    curr_ticker_info[2] = ori_ticker['high'].tolist()
    curr_ticker_info[3] = ori_ticker['low'].tolist()
    curr_ticker_info[4] = ori_ticker['close'].tolist()

    curr_ticker_pair = [curr_ticker, get_quote_data(curr_ticker)['longName']]
    tnews = news.get_yf_rss(curr_ticker)

    ticker_news = []
    for n in tnews:
        temp = n['published'].split('2021')[0] + '2021'
        ticker_news.append([n['title'], n['link'], temp, n['summary']])




    purchased_stocks = []
    temp_list = get_db().cursor().execute(
        "SELECT DISTINCT ticker, shares, cost FROM users_current WHERE username = ?", [username]
        ).fetchall()

    for temp in temp_list:
        t, s, c = temp['ticker'], temp['shares'], temp['cost']
        p = round(float(get_live_price(t)), 2)

        diff = round(((p * s) - (s * c)), 2)
        if diff > 0:
            diff = "+" + str(diff)
            purchased_stocks.append([str(t), str(s), str(c), diff, 'v1'])
        elif diff < 0:
            diff = str(diff)
            purchased_stocks.append([str(t), str(s), str(c), diff, 'v2'])
        else:
            purchased_stocks.append([str(t), str(s), str(c), diff, 'v0'])


    # 1. Get User Data 
    # 2. Get User Current Purchase Stocks
    # 3. Render User Watchlist

    # Fix - get user information.
    user_info = {}

    user_stats = get_db().cursor().\
                  execute("SELECT DISTINCT ticker, return, status FROM users_historical WHERE username = ?",\
                           [username]).fetchall()

    t, r, s = [], [], []
    for stats in user_stats:
        t.append(stats['ticker'])
        r.append(stats['return'])
        s.append(stats['status'])

    user_stat = pd.DataFrame({'ticker': t, 'return': r, 'status': s})

    user_stat0 = user_stat[user_stat['status'] == 0]
    user_stat1 = user_stat[user_stat['status'] == 1]
    user_stat2 = user_stat[user_stat['status'] == 2]


    select_sql = '''SELECT DISTINCT cash FROM users_finance WHERE username = ?'''
    user_info[1] = get_db().cursor().execute(select_sql, [username]).fetchone()['cash']
    user_info[2] = round(sum(user_stat['return']), 2)
    user_info[3] = user_stat2.shape[0]
    user_info[4] = user_stat1.shape[0]
    user_info[5] = user_stat0.shape[0]
    
    if flask.request.method == 'POST' and "sell_stocks" in flask.request.form:
        
        sell_ticker = flask.request.form['sell_stocks']
        temp_list = get_db().cursor().execute(
                    "SELECT * FROM users_current WHERE username = ? AND ticker = ?",\
                    [username, sell_ticker]).fetchone()

        ts, tc = temp_list['shares'], temp_list['cost']
        cp = round(float(get_live_price(sell_ticker)), 2)

        diff = round(((cp * ts) - (ts * tc)), 2)
        status = 1
        if diff > 5.00:
            status = 2
        elif diff < -5.00:
            status = 0

        insert_sql = '''INSERT INTO users_historical(username, ticker, return, status) VALUES (?, ?, ?, ?)'''
        get_db().cursor().execute(insert_sql, (username, sell_ticker, diff, status))

        delete_sql = '''DELETE FROM users_current WHERE username = ? AND ticker = ?'''
        get_db().cursor().execute(delete_sql, (username, sell_ticker))

        curr_cash = get_db().cursor().execute(
                    "SELECT cash FROM users_finance WHERE username = ?",\
                    [username]).fetchone()['cash']

        curr_cash = float(curr_cash) + diff
        update_sql = '''UPDATE users_finance SET cash = ? WHERE username = ?'''
        get_db().cursor().execute(update_sql, (curr_cash, username))

        #{'username': 'chinhau', 'ticker': 'PFE', 'shares': 50, 'cost': 35.96, 'active': 1}

        #sql_string2 = '''INSERT INTO users_finance(username, cash)
        #                VALUES (?, ?)'''
        #get_db().cursor().execute(sql_string2, (username, 1000.00))

        #print(temp_list)
        flash('You have successfully sold ' + sell_ticker + " & earned " + str(diff) + "!" , "success")
        return flask.redirect(url_for('main_page', curr_ticker=curr_ticker))
    
    elif flask.request.method == 'POST' and "remove-watchlist" in flask.request.form:
        delete_sql = '''DELETE FROM users_watchlist WHERE username = ? AND ticker = ?'''
        get_db().cursor().execute(delete_sql, (username, flask.request.form['remove-watchlist']))
        flash(flask.request.form['remove-watchlist'] + ' has been removed from your watchlist!' , "success")
        return flask.redirect(url_for('main_page', curr_ticker=curr_ticker))


    return flask.render_template("main_page.html", v_01=user_info, v_02 = curr_ticker_info,\
                                 v_03=purchased_stocks, v_04=curr_ticker_pair, v_05=watchlist, v_06=ticker_news)




@website.app.route('/update/<tickers>/', methods=['POST'])
def update(tickers):
    return jsonify({
        'stock_price': round(float(get_live_price(tickers)), 2)
    })

def classify1(pdiff):

    if pdiff > 10.0:
        return "rgba(49, 85, 122, 1)"
    return "rgba(221, 227, 234, 1)"

def classify2(pdiff):

    if pdiff > 20.0:
        return "rgba(49, 85, 122, 1)"
    return "rgba(221, 227, 234, 1)"

def classify3(pdiff):

    if pdiff > 50.0:
        return "rgba(169, 20, 20, 1)"
    elif pdiff > 15.0:
        return "rgba(222, 111, 111, 1)"
    return "rgba(221, 227, 234, 1)"

def classify4(pdiff):

    if pdiff > 10.0:
        return "rgba(169, 20, 20, 1)"
    elif pdiff > 5.0:
        return "rgba(222, 111, 111, 1)"
    return "rgba(221, 227, 234, 1)"

def stock_recommendations():

    d1 = datetime.date.today() - datetime.timedelta(days=1)
    d2 = datetime.date.today() - datetime.timedelta(days=20)

    ddata = get_db().cursor().execute("SELECT DISTINCT dates, tickers FROM historical_data WHERE dates BETWEEN ? AND ?", [d2, d1])\
               .fetchall()
    
    df = pd.DataFrame(ddata)
    df['mprice'], df['rprice'], df['price_diff'], df['percentage_diff'] = np.vectorize(stock_func)(df['tickers'], df['dates'])
    print(df.shape)
    df = df[df['mprice'] >= 1.5]
    print(df.shape)
    df = df[df['price_diff'] >= 0]
    print(df.shape)
    df = df[df['percentage_diff'] >= 0]
    print(df.shape)

    return df

def stock_func(tickers, edate):
    
    # Get date.

    edate = datetime.datetime.strptime(edate, "%Y-%m-%d") + datetime.timedelta(days=1)
    edate = edate.strftime('%Y-%m-%d') 
    # Get ticker data.
    temp = None
    try:
        temp = pd.DataFrame(get_data(tickers, start_date=edate))
    except:
        return 0.0, 0.0, 0.0, 0.0

    temp = temp[['high']]
    temp = temp['high'].tolist()
    rows = len(temp)

    if rows <= 2:
        return 0.0, 0.0, 0.0, 0.0
    elif rows == 3:
        tmin, trec = temp[0], max(temp[-1], (temp[-2] + temp[-1])/2)
    elif rows == 4:
        tmin, trec = min(temp), max((temp[-3] + temp[-2] + temp[-1])/3, (temp[-2] + temp[-1])/2)
    else:
        tmin, trec = min(temp), max((temp[-3] + temp[-2] + temp[-1])/3, (temp[-2] + temp[-1])/2)
    
    
    price_c = trec - tmin
    perct_c = (trec-tmin)/tmin*100

    if pd.isna(trec) or pd.isna(price_c) or pd.isna(perct_c):
        return 0.0, 0.0, 0.0, 0.0

    return round(tmin, 3), round(trec, 3), round(price_c, 3), round(perct_c, 3)   

def retrieve_personal_record(username):

    get_data = get_db().cursor().execute(
               "SELECT DISTINCT * FROM historical_purchase WHERE username = ?", username).fetchall()
    return pd.DataFrame(get_data)

def retrieve_data():
    '''Retrieve all historical data from our database.'''
    get_data = get_db().cursor().execute("SELECT DISTINCT * FROM historical_data")\
               .fetchall()
    df = pd.DataFrame(get_data)
    return df

def check_usersession():

    return 'username' in flask.session

def handle_password(input_password):
    sha = hashlib.sha512()
    sha.update(str('salt').encode('utf-8'))
    sha.update(str(input_password).encode('utf-8'))
    hashed_p = sha.hexdigest()
    return "$" + hashed_p





