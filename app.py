from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "playlist_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///playlist.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(150), nullable=False)
    album = db.Column(db.String(150), nullable=False)

@app.route('/')
def index():
    songs = Song.query.all()
    return render_template('index.html', songs=songs)


@app.route("/add_song", methods=["GET", "POST"])
def add_song():
    if request.method == "POST":
        title = request.form["title"]
        artist = request.form["artist"]
        album = request.form["album"]

        new_song = Song(title=title, artist=artist, album=album)
        db.session.add(new_song)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("add.html")

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_song(id):
    song = Song.query.get_or_404(id)
    if request.method == 'POST':
        song.title = request.form['title']
        song.artist = request.form['artist']
        song.album = request.form['album']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', song=song)

@app.route('/delete/<int:id>')
def delete_song(id):
    song = Song.query.get_or_404(id)
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    song = Song.query.get_or_404(id)
    song.title = request.form['title']
    song.artist = request.form['artist']
    song.album = request.form['album']
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
