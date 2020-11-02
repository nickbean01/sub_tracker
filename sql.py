create_subreddits_tbl = '''
CREATE TABLE subreddits(
    id INTEGER PRIMARY KEY,
    subreddit TEXT UNIQUE
)
'''

create_subreddit_info_tbl = '''
CREATE TABLE subreddit_info (
    id INTEGER PRIMARY KEY,
    subreddit_id INTEGER,
    num_active_users INTEGER,
    num_subscribers INTEGER,
    timestamp TEXT,
    FOREIGN KEY (subreddit_id) REFERENCES subreddits (id)
)
'''

_create_active_users_tbl = '''
CREATE TABLE active_users(
    id INTEGER PRIMARY KEY,
    num_active_users INTEGER,
    subreddit TEXT,
    timestamp TEXT
)
'''

insert_to_sub_info = '''
INSERT INTO subreddit_info
(num_active_users, num_subscribers, subreddit_id, timestamp)
VALUES ({}, {}, {}, "{}")
'''

insert_new_subreddit = '''
INSERT INTO subreddits (subreddit)
VALUES ("{}")
'''

get_subreddit = '''
SELECT * FROM subreddits
WHERE subreddit = "{}"
'''

get_subreddit_info = '''
SELECT * FROM subreddit_info AS si
LEFT JOIN subreddits AS s
ON si.subreddit_id == s.id
'''
