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
