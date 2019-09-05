import psycopg2
import os
import time
import re
import requests
from base64 import b64encode

from passlib.hash import sha256_crypt

from flask import render_template

DATABASE_URL = os.environ['DATABASE_URL']
CLIENT_ID = os.environ['IMGUR_CLIENT_ID']

def uploadImage(img):
    headers = {
        'Authorization': 'Client-ID ' +  CLIENT_ID
    }

    payload = {'image': b64encode(img.read())}
    url = "https://api.imgur.com/3/image"

    resp = requests.post(url, headers=headers, data=payload)
    lnk = resp.json()['data']['link']
    return lnk

def notFound():
    return render_template("notFound.html"), 404

def file_from_store(file_name):
    """
    Get file contents to return from storage.

    Args:
    - file_name: name of file to retrieve
    """
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    try:
        c.execute("SELECT title, content FROM posts WHERE slug = %s", (file_name,))
        title, content = c.fetchall()[0]
        return render_template("post.html", title=title, content=content)
    except Exception as e:
        print(e)
        return notFound()

def get_content(slug):
    # TODO
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("SELECT title, content FROM posts WHERE slug = %s", (slug,))

def get_posts():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("SELECT slug, title, thumb, description FROM posts WHERE publish_date < %s;", (int(time.time()),))
    posts = c.fetchall()
    ret = [{"href": p[0],
            "title": p[1],
            "image": p[2],
            "description": p[3]} for p in posts]

    conn.close()
    return ret

def get_published_posts():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("SELECT title, slug FROM posts WHERE publish_date < %s;", (int(time.time()),))
    posts = c.fetchall()
    ret = [{"title": p[0],
            "slug": p[1]} for p in posts]

    conn.close()
    return ret

def get_unpublished_posts():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("SELECT title, slug FROM posts WHERE publish_date > %s;", (int(time.time()),))
    posts = c.fetchall()
    ret = [{"title": p[0],
            "slug": p[1]} for p in posts]

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

def create_post(title, author_id, publish_date, thumb, description, content):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()

    slug = re.sub(r'\W+', '', title).lower()

    while c.execute("SELECT * FROM posts WHERE slug = %s", (slug,)) != None:
        slug += str(os.urandom(2))

    c.execute("INSERT INTO posts VALUES ({}, {}, {}, {}, {}, {}, {}, {})".format(repr(title), repr(slug), int(time.time()), repr(author_id), repr(description), repr(thumb), int(time.mktime(time.strptime(publish_date, '%Y-%m-%d'))), repr(content)))
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
    c.execute("INSERT INTO users VALUES (%s, %s, %s);", (username, sha256_crypt.hash(password), 3))
    conn.commit()
    conn.close()

def set_password(username, password):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("UPDATE users SET pass_hash='%s' WHERE username='%s';", (sha256_crypt.hash(password), username))
    conn.commit()
    conn.close()

def set_privileges(username, privs):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    c = conn.cursor()
    c.execute("UPDATE users SET priveleges=%s WHERE username=%s;", (privs, username))
    conn.commit()
    conn.close()
