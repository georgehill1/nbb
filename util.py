import psycopg2

import os, time

from passlib.hash import sha256_crypt

DATABASE_URL = os.environ['DATABASE_URL']

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
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("SELECT * FROM posts;")
    posts = c.fetchall()
    ret = [{"href": p[1],
            "title": p[0],
            "image": p[5],
            "description": p[4]} for p in posts]

    conn.close()
    return ret

def get_priv_choices(user):
    lvl = privFromUser(user)
    ret = []
    if lvl <= 3:
        ret.append({"val": 3, "desc": privLookup(3)})
    if lvl <= 2:
        ret.append({"val": 2, "desc": privLookup(2)})
    if lvl <= 1:
        ret.append({"val": 1, "desc": privLookup(1)})
    if lvl == 0:
        ret.append({"val": 0, "desc": privLookup(0)})
    return ret

def privFromUser(user):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("SELECT priveleges FROM users WHERE username = '{}';".format(user))
    users = c.fetchone()
    ret = int(users[0])
    conn.close()
    return ret

def privLookup(privs):
    # privileges
    # 0 - admin - create and remove users +
    # 1 - writer - create, and remove posts +
    # 2 - publisher - publish posts
    # 3 - nothing - nothing
    if privs == 0:
        return "Administrator"
    if privs == 1:
        return "Writer"
    if privs == 2:
        return "Publisher"
    if privs == 3:
        return "None"
    return "Error"

def get_users():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("SELECT * FROM users;")
    users = c.fetchall()
    ret = [{"user": u[0],
            "priv": privLookup(u[2])
            } for u in users]

    conn.close()
    return ret

def add_post_to_database(title, slug, author_id, publish_date, thumb, description, content):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()

    # TODO - put actual post in store

    # title TEXT, slug TEXT PRIMARY KEY, timestamp INTEGER, author_id INTEGER, description TEXT, thumb TEXT, publish_date INTEGER)

    c.execute("INSERT INTO posts VALUES ({}, {}, {}, {}, {}, {}, {})".format(repr(title), repr(slug), int(time.time()), author_id, repr(description), repr(thumb), int(publish_date)))
    conn.commit()

    conn.close()

def validate_creds(username, password):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    valid = False
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = '{}';".format(username))
    row = c.fetchone()
    if row:
        valid = sha256_crypt.verify(password, row[1])
    else:
        conn.close()
        return valid, None
    return valid, row[0]

def create_user(username, password):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
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
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("UPDATE users SET pass_hash=? WHERE username=?;", (sha256_crypt.hash(password), username))
    conn.commit()
    conn.close()

def set_privileges(username, privs):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("UPDATE users SET pass_hash=? WHERE username=?;", (privs, username))
    conn.commit()
    conn.close()

#add_post_to_database("Test Post", "testpost", 0, time.time(), "/res/david.jpg", "A second test post entry.")
#print(create_user("admin", "admin"))
#set_password("admin", "michelle obama")
#print(validate_creds("admin", "michelle obama"))
