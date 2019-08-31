import sqlite3

import time

from passlib.hash import sha256_crypt

def file_from_store(file_name):
    """
    Get file contents to return from storage.

    Args:
    - file_name: name of file to retrieve
    """
    with open(file_name, 'r') as f:
        content = f.read()
    
    return content

def get_posts():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM posts;")
    posts = c.fetchall()
    ret = [{"href": p[1],
            "title": p[0],
            "image": p[5],
            "description": p[4]} for p in posts]

    conn.close()
    return ret

def add_post_to_database(title, slug, author_id, publish_date, thumb, description, content):
    # TODO - get database from GCS
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # TODO - put actual post in store

    # title TEXT, slug TEXT PRIMARY KEY, timestamp INTEGER, author_id INTEGER, description TEXT, thumb TEXT, publish_date INTEGER)

    c.execute("INSERT INTO posts VALUES ({}, {}, {}, {}, {}, {}, {})".format(repr(title), repr(slug), int(time.time()), author_id, repr(description), repr(thumb), int(publish_date)))
    conn.commit()

    conn.close()
    # TODO - post database to GCS

def validate_creds(username, password):
    conn = sqlite3.connect('database.db')
    valid = False
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = '{}';".format(username))
    row = c.fetchone()
    if row:
        valid = sha256_crypt.verify(password, row[1])
    else:
        conn.close()
        return valid, None

    # privileges
    # 0 - admin
    # 1 - writer
    # 2 - publisher
    # 3 - nothing


    return valid, row[0]

def create_user(username, password):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Check existing
    c.execute("SELECT * FROM users WHERE username={};".format(repr(username)))
    existing = c.fetchall()
    if existing:
        conn.close()
        return "USER EXISTS"
    # Insert
    c.execute("INSERT INTO users VALUES (?, ?, ?);", (username, sha256_crypt.hash(password), 3))
    conn.commit()
    conn.close()

def set_password(username, password):
    # TODO - 
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET pass_hash=? WHERE username=?;", (sha256_crypt.hash(password), username))
    conn.commit()
    conn.close()

#add_post_to_database("Test Post", "testpost", 0, time.time(), "/res/david.jpg", "A second test post entry.")
#print(create_user("admin", "admin"))
#set_password("admin", "michelle obama")
#print(validate_creds("admin", "michelle obama"))