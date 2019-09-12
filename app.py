from util import file_from_store, get_posts, validate_creds, get_users, get_priv_choices, privFromUser, create_user, set_password, uploadImage, create_post, set_privileges, get_published_posts, get_unpublished_posts

from flask import Flask, render_template, send_file, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import random

import os
import json

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

def ensure_logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect('/login')
        return fn(*args, **kwargs)
    return wrapper
def ensure_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not privFromUser(session.get('user_id')) == 0:
            return redirect("/auth_too_low")
        return fn(*args, **kwargs)
    return wrapper
def ensure_writer(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not privFromUser(session.get('user_id')) <= 1:
            return redirect("/auth_too_low")
        return fn(*args, **kwargs)
    return wrapper
def ensure_publisher(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not privFromUser(session.get('user_id')) <= 2:
            return redirect("/auth_too_low")
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def home_page():
    return render_template("index.html", posts=get_posts())

@app.route("/res/<path:image_name>")
def get_image(image_name):
    return send_file("img/" + image_name)

@app.route("/favicon.ico")
def get_favicon():
    return get_image("favicon.ico")

# JSON spec
# [
# {
# "type": "text",
# "content": "Lipsum crap",
# }
# "type": "image",
# "content": "<imgur embed code>"
# ]

@app.route("/login", methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logged_in, user = validate_creds(username, password)
        if not logged_in:
            error = 'Invalid Credentials. Please try again.'
        else:
            session['user_id'] = user
            return redirect('/settings')
    if session.get('user_id'):
        return redirect('/settings')
    return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect("/")

@app.route("/upload", methods=['GET', 'POST'])
@ensure_logged_in
@ensure_writer
def upload():
    if request.method == 'POST':
        try:
            file = request.files['thumb']
            uploadedThumb = uploadImage(file)
            create_post(request.form['title'], session.get('user_id'), request.form['publish'], uploadedThumb, request.form['description'], request.form['content'])
            return "Success!"
        except Exception as e:
            print(e)
            return "failed"
        return redirect("/upload")
    return render_template("upload.html", privLvl = privFromUser(session.get('user_id')), preContent="Here is some sample content.")

@app.route("/posts")
@ensure_logged_in
@ensure_publisher
def unpublishedposts():
    published = get_published_posts()
    unpublished = get_unpublished_posts()

    return render_template("unpublished.html", published=published, unpublished=unpublished)

@app.route("/auth_too_low")
@ensure_logged_in
def low_auth():
    return "<!DOCTYPE html><html lang=\"en\" dir=\"ltr\"><head><meta charset=\"utf-8\"><title>Nerdboard</title></head><body><h1>Not Authorised</h1><p>Sorry, you don't have the required permissions to complete this operation. <a onclick=\"window.history.back();\">Go back.</a></p></body></html>"

@app.route("/settings")
@app.route("/users")
@ensure_logged_in
@ensure_publisher
def settings():
    return render_template("settings.html", users=get_users(), privLvl = privFromUser(session.get('user_id')), user=session.get('user_id'))

@app.route("/adduser", methods=['GET', 'POST'])
@ensure_logged_in
@ensure_admin
def adduser():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['pass']
        privileges = request.form['privileges']
        error = create_user(username, password)
        error = set_privileges(username, privileges)
        if error == None:
            return redirect("/settings")
    return render_template("add_user.html", privs=get_priv_choices(session.get('user_id')), error=error)

@app.route("/createuser", methods=['GET', 'POST'])
def createuser():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_conf = request.form['password-conf']
        if password != password_conf:
            error = "Passwords do not match"
        else:
            error = create_user(username, password)
            logged_in, user = validate_creds(username, password)
            if not logged_in:
                error = 'Invalid Credentials. Please try again.'
            if error == None:
                session['user_id'] = user
                return redirect("/settings")
    return render_template("createuser.html", error=error)

@app.route("/modifyuser/<username>", methods=['GET', 'POST'])
@ensure_logged_in
def modifyuser(username):
    error = None
    if privFromUser(session.get('user_id')) != 0:
        if session.get('user_id') != username:
            return redirect("/auth_too_low")
    if request.method == 'POST':
        try:
            password = request.form['password']
            password_conf = request.form['password-conf']
        except:
            password = None
            password_conf = None
        try:
            privileges = request.form['privileges']
        except:
            privileges = None
        if password_conf != password and password != None:
            error = "Passwords do not match!"
        elif privileges != None:
            set_privileges(username, privileges)
        elif password != None and password_conf != None:
            set_password(username, password)
    return render_template("modifyuser.html", username=username, privs=get_priv_choices(session.get('user_id')), error=error)

@app.route("/metrics")
@ensure_logged_in
def metrics():
    return redirect("https://analytics.google.com")

@app.route("/random.html")
def rando():
    posts = get_posts();
    r = random.randint(0, len(posts)-1)

    return redirect(posts[r]['href'])

@app.route("/about.html")
def about():
    return render_template("about.html")

@app.route("/contact.html")
def contact():
    return render_template("contact.html")

@app.route("/styles/<stylename>")
def style(stylename):
    return app.send_static_file(stylename)

@app.route("/imgUpload", methods=['GET', 'POST'])
@ensure_logged_in
def imgUpload():
    try:
        files = request.files.getlist('upload')
        for file in files:
            link = uploadImage(file)
        return json.dumps({"uploaded": True, "url": link})
    except Exception as e:
        print("Error:", e)
        return json.dumps({"uploaded": False, "error": {"message": "could not upload this image"}})

@app.route("/<postname>")
def get_post(postname):
    return file_from_store(postname)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=os.environ.get("PORT"))
