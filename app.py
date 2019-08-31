from util import file_from_store, get_posts, validate_creds, get_users, get_priv_choices, privFromUser, create_user, set_password

from flask import Flask, render_template, send_file, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import random

import os

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = r"e,4zLtWXcD.5Ca^3Mm^!'l+6H#S>W4c)AI2K<:}}cXVq{D2YVs]C6qW-cGEm&ZZ"

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
            return redirect('/upload')
    if session.get('user_id'):
        return redirect('/upload')
    return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect("/login")

@app.route("/upload", methods=['GET', 'POST'])
@ensure_logged_in
def secret():
    return render_template("upload.html")

@app.route("/auth_too_low")
@ensure_logged_in
def low_auth():
    return "<!DOCTYPE html><html lang=\"en\" dir=\"ltr\"><head><meta charset=\"utf-8\"><title>Nerdboard</title></head><body><h1>Not Authorised</h1><p>Sorry, you don't have the required permissions to complete this operation. <a onclick=\"window.history.back();\">Go back.</a></p></body></html>"

@app.route("/settings")
@app.route("/users")
@ensure_logged_in
def settings():
    return render_template("settings.html", users=get_users())

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
        if error == None:
            return redirect("/settings")
    return render_template("add_user.html", privs=get_priv_choices(session.get('user_id')), error=error)

@app.route("/metrics")
@ensure_logged_in
def metrics():
    return redirect("analytics.google.com")

@app.route("/random.html")
def rando():
    # TODO
    posts = get_posts();
    r = random.randint(0, len(posts))

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

@app.route("/<postname>")
def get_post(postname):
    if postname[-5] == ".html":
        return file_from_store("posts/" + postname)
    else:
        return file_from_store("posts/" + postname + ".html")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=os.environ.get("PORT"))
