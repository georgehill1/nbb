from util import file_from_store, get_posts, validate_creds

from flask import Flask, render_template, send_file, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = r"e,4zLtWXcD.5Ca^3Mm^!'l+6H#S>W4c)AI2K<:}}cXVq{D2YVs]C6qW-cGEm&ZZ"

def ensure_logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect('/login')
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
    return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect("/login")

@app.route("/upload", methods=['GET', 'POST'])
@ensure_logged_in
def secret():
    return render_template("upload.html")


@app.route("/<postname>")
def get_post(postname):
    return file_from_store("posts/" + postname)

if __name__ == '__main__':
    app.run(debug=True)