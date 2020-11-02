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


def db_transaction(func):
    def wrapper():
        try:
            con = db_connect()
            c = con.cursor()
            func()
        except sqlite3.Error as e:
            print(e)
        finally:
            if con:
                con.close()
    return wrapper



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


def get_num_active_users(soup):
    ''' find number of active users by searching for
    <p class="users-online"><span class="number"></span</p>

    Parameters:
        soup (BeautifulSoup): html from a subreddit
    Returns:
        (int): number of active users on a subreddit
    '''
    span = soup.findAll('p', {'class': 'users-online'})[0] \
        .findAll('span', {'class': 'number'})[0]
    return int(float(span.text.strip().replace(',', '')))


def get_num_subscribers(soup):
    ''' find number of subscribers

    Parameters:
        soup (BeautifulSoup): html from a subreddit
    Returns:
        (int): number of active users on a subreddit
    '''
    span = soup.findAll('span', {'class': 'subscribers'})[0] \
        .findAll('span', {'class': 'number'})[0]
    return int(float(span.text.strip().replace(',', '')))


def get_subreddit_info(sub):
    ''' get number of active users, and subscribers of a subreddit
    data currently stored in sqlite

    Parameters:
        sub (str): name of a subreddit
    '''
    ts = datetime.datetime.utcnow().isoformat()

    soup = get_subreddit_data(sub=sub)
    try:
        con = db_connect()
        c = con.cursor()

        # get subreddit_id from subreddits table
        sub_df = pd.read_sql_query(sql.get_subreddit.format(sub), con)
        if len(sub_df.index) == 0:
            insert_new_subreddit()
            sub_df = pd.read_sql_query(sql.get_subreddit.format(sub), con)
        sub_id = sub_df.iloc[0, 0]

        num_users = get_num_active_users(soup)
        num_subscribers = get_num_subscribers(soup)

        print('{} of {} in subreddit {}({}) at {}'.format(
            num_users, num_subscribers, sub, sub_id, ts
        ))

        # insert new record to active_users table
        c.execute(sql.insert_to_sub_info.format(
            num_users, num_subscribers, sub_id, ts
        ))
        con.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        if con:
            con.close()


def track_active_users():
    for sub in config.SUBREDDITS:
        get_subreddit_info(sub)


def graph_active_users():
    try:
        con = db_connect()
        df = pd.read_sql_query(sql.get_subreddit_info, con)

        df['dt'] = pd.to_datetime(df['timestamp'])

        df.to_csv('subreddit_info.csv')

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

