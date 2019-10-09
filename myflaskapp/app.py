from flask import Flask, render_template, flash, redirect, url_for, request, session, logging
#from Recommendations import popular_recommender
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from functools import wraps
import spotipy
import spotipy.util as util
import json

app = Flask(__name__)

#config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#initialize MySQL
mysql = MySQL(app)

app.jinja_env.filters['zip'] = zip

token = util.prompt_for_user_token(username='a89c3r3q6g1u7k7ndj1e0j2rf',scope='playlist-modify-public',client_id='',client_secret='',redirect_uri='https://google.com/')
spotifyObject = spotipy.Spotify(auth=token)

user = spotifyObject.current_user()

popular_songs = popular_recommender()

@app.route('/')
def intro():
    return render_template("intro.html")

@app.route('/popularity')
def popular():
    popular_tracks = []
    popular_artists = []
    popular_ids = []
    json_of_popular_songs=spotifyObject.user_playlist_tracks(user['display_name'], playlist_id='37i9dQZEVXbMDoHDwVN2tF',limit=10)
    for i in range(10):
      popular_tracks.append(json_of_popular_songs['items'][i]['track']['name'])
      popular_artists.append(json_of_popular_songs['items'][i]['track']['artists'][0]['name'])
      popular_ids.append(json_of_popular_songs['items'][i]['track']['id'])
      
    popular = zip(popular_tracks,popular_artists)
    list_of_popular=list(popular)
    popular_songs = list_of_popular
    return render_template("popularity.html", popularSongs = popular_songs,songID = popular_ids)

@app.route('/similarity')
def similar():
    return render_template("similarity.html")

@app.route('/similarity', methods = ["GET","POST"] )
def get_data():
    if request.method == "POST":
      track_name = request.form["song"]
      artist_name = request.form["artist"]
      result_of_artist_name = spotifyObject.search(artist_name,1,0,"artist")
      #print(json.dumps(result_of_artist_name, sort_keys=True, indent=4))
      artist_id = result_of_artist_name['artists']['items'][0]['id']  
      result_of_track_name = spotifyObject.search(track_name,1,0,"track")
      #print(json.dumps(result_of_artist_name, sort_keys=True, indent=4))
      track_id = result_of_track_name['tracks']['items'][0]['id']
      json_of_recommendations = spotifyObject.recommendations(seed_artists= [artist_id], seed_tracks = [track_id], limit=10)
      #print(json.dumps(json_of_recommendations, sort_keys=True, indent=4))
      recommended_artists = []
      recommended_tracks = []
      recommended_ids = []
      for i in range(10):
        recommended_tracks.append(json_of_recommendations['tracks'][i]['name'])
        recommended_artists.append(json_of_recommendations['tracks'][i]['artists'][0]['name'])
        recommended_ids.append(json_of_recommendations['tracks'][i]['id'])
      
      recommendations = zip(recommended_tracks,recommended_artists)
      list_of_recommendations = list(recommendations)
      print(list_of_recommendations[0][1])
      print(list_of_recommendations)

      similar_songs = list_of_recommendations
    return render_template("similarity.html", similarSongs = similar_songs, songID = recommended_ids)  

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == 'POST':
        name = request.form["name"]
        email = request.form["email"]
        username = request.form["username"]
        password = sha256_crypt.encrypt(str(request.form["password"]))
        #create cursor
        cur = mysql.connection.cursor()
        #cursor and database
        cur.execute("INSERT INTO users (name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        #commit
        mysql.connection.commit()
        #close cursor
        cur.close()
        #flash message
        flash("You are now registered and can log in.","success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods = ['GET','POST'])
def login():
  if request.method == 'POST':
    username = request.form["username"]
    password_login = request.form["password"]
    #cursor obj created
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
    if result > 0:
      data = cur.fetchone()
      password = data['password']
      if sha256_crypt.verify(password_login, password):
        session['logged_in'] = True
        session['username'] = username
        flash("Logged In Successfully!", "success")
        return redirect(url_for('library'))
      else:
        error = "Incorrect Password!"
        return render_template("login.html", error=error)
      cur.close()
    else:
        error = "User is not registered."
        return render_template("login.html", error=error)
  return render_template("login.html")

def is_logged_in(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else:
      flash("Please log in to access your library!","danger")
      return redirect(url_for("login"))
  return wrap

@app.route('/logout')
@is_logged_in
def logout():
  session.clear()
  flash("Logged out successfully!","success")
  return redirect(url_for('login'))

@app.route('/library')
@is_logged_in
def library():
  #create cursor
  cur = mysql.connection.cursor()
  #execute cursor and query
  result = cur.execute("SELECT song,song_id FROM songs WHERE username = %s",[session['username']])
  songs = cur.fetchall()
  #loading data to library
  if result > 0:
    return render_template('library.html', songs=songs)
  else:
    msg = 'No Articles Found'
    return render_template('library.html', msg=msg)
  #close the db connection
  cur.close()
  

@app.route('/add_song/<song>/<song_id>',methods=['GET','POST'])
@is_logged_in
def add_song(song,song_id):
  print(song)
  print(song_id)
  if request.method == 'GET':
    #create cursor
    cur = mysql.connection.cursor()
    #execute cursor and query
    cur.execute("INSERT INTO songs(song,username,song_id) VALUES(%s, %s, %s)",(song,session['username'],song_id))
    #commit
    mysql.connection.commit()
    #close connection
    cur.close()

    flash('Song added successfully','success')
    return redirect(url_for('library'))
  return render_template('library.html')

@app.route('/delete_song/<song_id>',methods=['GET','POST'])
@is_logged_in
def delete_song(song_id):
  print(song_id)
  if request.method == 'GET':
    #create cursor
    cur = mysql.connection.cursor()
    #execute cursor and query
    cur.execute("DELETE FROM songs WHERE song_id = %s",[song_id])
    #commit
    mysql.connection.commit()
    #close connection
    cur.close()

    flash('Song deleted successfully','success')
    return redirect(url_for('library'))
  return render_template('library.html')


if __name__=="__main__":
    app.secret_key='secret123'
    app.run(debug=True)
