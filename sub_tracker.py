from bs4 import BeautifulSoup

import argparse
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import pprint
import requests
import seaborn as sns
import sqlite3

import config
import sql


def db_connect(db_path=config.DB_PATH):
    con = sqlite3.connect(db_path)
    return con


def add_new_subreddit(sub):
    try:
        con = db_connect()
        c = con.cursor()
        df = pd.read_sql_query(sql.get_subreddit.format(sub), con)
        if len(df.index) == 0:
            print('adding subreddit: {}'.format(sub))
            c.execute(sql.insert_new_subreddit.format(sub))
        con.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        con.close()


def setup_db():
    try:
        con = db_connect()
        c = con.cursor()

        #c.execute(sql.create_subreddits_tbl)
        #c.execute(sql.create_active_users_tbl)

        con.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        con.close()


def get_subreddit_data(sub):
    page = requests.get(
        'https://old.reddit.com/r/{}'.format(sub),
        headers={
            'User-agent': config.USER_AGENT,
            'Cache-Control': 'no-cache'
        }
    )
    if not page.status_code == 200:
        raise Exception('failed to get subreddit data:\n{}'.format(page.status_code))

    soup = BeautifulSoup(page.text, 'html.parser')
    return soup


def get_cached_data():
    soup = BeautifulSoup(open('tmp.out'), 'html.parser')
    return soup


def insert_active_users(num_users, sub, ts):
    try:
        con = db_connect()
        c = con.cursor()
        c.execute(sql.insert_to_active_users.format(num_users, sub, ts))
        con.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        if con:
            con.close()


def get_subreddit_info(sub):
    ts = datetime.datetime.utcnow().isoformat()

    soup = get_subreddit_data(sub=sub)

    users_online = soup.findAll('p', {'class': 'users-online'})[0]
    users_online_span = users_online.findAll('span', {'class': 'number'})[0]
    num_text = users_online_span.text.strip().replace(',', '')
    num_active_users = int(float(num_text))

    print('{} in subreddit {} at {}'.format(
        num_active_users, sub, ts
    ))

    insert_active_users(num_active_users, sub, ts)


def track_active_users():
    for sub in config.SUBREDDITS:
        get_subreddit_info(sub)


def graph_active_users():
    q = '''SELECT num_active_users, subreddit, timestamp
        FROM active_users;
    '''
    try:
        con = db_connect()
        df = pd.read_sql_query(q.format(), con)

        #pprint.pprint(df)
        #print(df.dtypes)

        df['dt'] = pd.to_datetime(df['timestamp'])

        #pprint.pprint(df)
        #print(df.dtypes)
        df.to_csv('active_users.csv')

        sns.set_style("darkgrid")
        sns.lineplot(x='dt', y='num_active_users', hue='subreddit', data=df)
        plt.show()
    except sqlite3.Error as e:
        print(e)
    finally:
        if con:
            con.close()


def main():
    #setup_db()
    #raise Exception()
    parser = argparse.ArgumentParser()

    parser.add_argument('--get', action='store_true', required=False)
    parser.add_argument('--graph', action='store_true', required=False)

    args = parser.parse_args()
    if args.get:
        track_active_users()
    elif args.graph:
        graph_active_users()
    else:
        print('please enter "--get" or "--graph" or multiple')


if __name__ == '__main__':
    main()

