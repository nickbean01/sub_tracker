from bs4 import BeautifulSoup

import argparse
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import pprint
import requests
import seaborn as sns
import sqlite3


DEFAULT_DB_PATH = 'collapse_tracker.db'


create_active_users_tbl = '''
CREATE TABLE active_users(
id INTEGER PRIMARY KEY,
num_active_users INTEGER,
subreddit TEXT,
timestamp TEXT
)
'''

insert_to_active_users = '''
INSERT INTO active_users
(num_active_users, subreddit, timestamp)
VALUES ({}, "{}", "{}")
'''


def db_connect(db_path=DEFAULT_DB_PATH):
    con = sqlite3.connect(db_path)
    return con


def setup_db():
    try:
        con = db_connect()
        c = con.cursor()
        c.execute(create_active_users_tbl)
        con.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        con.close()


def get_subreddit_data(sub):
    page = requests.get(
        'https://old.reddit.com/r/{}'.format(sub),
        headers={'User-agent': ''}
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
        c.execute(insert_to_active_users.format(num_users, sub, ts))
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
    subs = [
        'anime_titties',
        'collapse',
        'futurology',
        'politics'
    ]
    for sub in subs:
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

