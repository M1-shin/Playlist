from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import uuid

app = Flask(__name__)
app.secret_key = "playlist_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///playlist.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    share_token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(150), nullable=False)
    album = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('songs', lazy=True))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to view that page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@app.route('/')
def index():
    user = current_user()
    if not user:
        return render_template('landing.html')
    songs = Song.query.filter_by(user_id=user.id).all()
    return render_template('index.html', songs=songs, user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        if not username or not email or not password:
            flash("Please fill out all fields.", "danger")
            return render_template('register.html')
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already taken.", "danger")
            return render_template('register.html')
        user = User(username=username, email=email)
        user.set_password(password)
        user.share_token = uuid.uuid4().hex
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username_or_email = request.form['username_or_email'].strip()
        password = request.form['password']

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user:
            if user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                flash(f"Welcome back, {user.username}!", "success")
                return redirect(url_for('index'))
            else:
                flash("Incorrect password. Please try again.", "danger")
        else:
            flash("No account found with that username or email.", "danger")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    user = current_user()
    return render_template('confirmlogout.html', user=user)

@app.route('/logout/confirm', methods=['POST'])
@login_required
def confirm_logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for('login'))


@app.route("/add_song", methods=["GET", "POST"])
@login_required
def add_song():
    user = current_user()
    if request.method == "POST":
        title = request.form["title"].strip()
        artist = request.form["artist"].strip()
        album = request.form["album"].strip()

        if not title or not artist or not album:
            flash("Please fill all fields.", "warning")
            return render_template("add.html")

        new_song = Song(title=title, artist=artist, album=album, user_id=user.id)
        db.session.add(new_song)
        db.session.commit()
        flash("Song added to your playlist.", "success")
        return redirect(url_for("index"))
    return render_template("add.html")

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_song(id):
    user = current_user()
    song = Song.query.get_or_404(id)
    if song.user_id != user.id:
        flash("You are not allowed to edit that song.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        song.title = request.form['title'].strip()
        song.artist = request.form['artist'].strip()
        song.album = request.form['album'].strip()
        db.session.commit()
        flash("Song updated.", "success")
        return redirect(url_for('index'))
    return render_template('edit.html', song=song)

@app.route('/delete/<int:id>', methods=['GET'])
@login_required
def delete_song(id):
    user = current_user()
    song = Song.query.get_or_404(id)
    if song.user_id != user.id:
        flash("You are not allowed to delete that song.", "danger")
        return redirect(url_for('index'))
    return render_template('delete.html', song=song)

@app.route('/delete/<int:id>/confirm', methods=['POST'])
@login_required
def confirm_delete(id):
    user = current_user()
    song = Song.query.get_or_404(id)
    if song.user_id != user.id:
        flash("You are not allowed to delete that song.", "danger")
        return redirect(url_for('index'))
    db.session.delete(song)
    db.session.commit()
    flash("Song deleted.", "info")
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update(id):
    user = current_user()
    song = Song.query.get_or_404(id)
    if song.user_id != user.id:
        flash("You are not allowed to update that song.", "danger")
        return redirect(url_for('index'))
    song.title = request.form['title'].strip()
    song.artist = request.form['artist'].strip()
    song.album = request.form['album'].strip()
    db.session.commit()
    flash("Song updated.", "success")
    return redirect(url_for('index'))

@app.route('/share')
@login_required
def share():
    user = current_user()
    link = url_for('shared_playlist', token=user.share_token, _external=True)
    return render_template('share.html', share_link=link, user=user)

@app.route('/share/regenerate')
@login_required
def share_regenerate():
    user = current_user()
    user.share_token = uuid.uuid4().hex
    db.session.commit()
    flash("Share link regenerated.", "success")
    return redirect(url_for('share'))

@app.route('/shared/<token>')
def shared_playlist(token):
    user = User.query.filter_by(share_token=token).first_or_404()
    songs = Song.query.filter_by(user_id=user.id).all()
    return render_template('shared.html', songs=songs, owner=user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
