import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth

from flask import Flask, request, url_for, session, redirect

# initializes Flask app
app = Flask(__name__)

# sets name of session cookie, random secret key to sign the cookie, and key for token info in the session dictionary
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = '02j029j0djkddijfo8j3jowjeo*(#*J)'
TOKEN_INFO = 'token_info'

# route to handle logging in
@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url() # creates a SpotifyOAuth instance and gets the authorization URL
    return redirect(auth_url) # redirects user to the authorization url

# routh to handle redirect URI after user authorization
@app.route('/redirect')
def redirect_page():
    session.clear() # clears session 
    code = request.args.get('code') # gets the authorization code from the request parameters
    token_info = create_spotify_oauth().get_access_token(code) # exchanges the authorization code for an access token and refresh token
    session[TOKEN_INFO] = token_info # saves the token info in the session
    return redirect(url_for('save_discover_weekly', external = True)) # redirects the user to save_discover_route

# route to save the Discover Weekly songs to a playlist
@app.route('/saveDiscoverWeekly')
def save_discover_weekly():
    try:
        token_info = get_token() # gets token info from session
    except: # if token info is not found, redirect user back to login route
        print("User not logged in")
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    current_playlists = sp.current_user_playlists()['items']
    user_id = sp.current_user()['id']

    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None

    # finds the discover weekly and saved weekly playlists
    for playlist in current_playlists:
        if(playlist['name'] == "Discover Weekly"):
            discover_weekly_playlist_id = playlist['id']
        if(playlist['name'] == "Saved Weekly"):
            saved_weekly_playlist_id = playlist['id']

    if not discover_weekly_playlist_id:
        return 'Discover Weekly not found'
    
    if not saved_weekly_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']
    
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']: # loops through each song in discover weekly, targeting songs by track uri, then adding each song uri into song_uris
        song_uri = song['track']['uri']
        song_uris.append(song_uri)
    
    user_id = sp.current_user()['id']
    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)
    return("success!")


# function to get the token info from the session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info: # if token info not found, redirect user to login route
        redirect(url_for('login', external=False))
    
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60

    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info



def create_spotify_oauth():
    return SpotifyOAuth(client_id = '1da85557ea054a9084d3d22539974f1d',
                        client_secret = '58d124fb711b4733ba9dd6f36e8f2a3b',
                        redirect_uri = url_for('redirect_page', _external= True),
                        scope = 'user-library-read playlist-modify-public playlist-modify-private'
    )

app.run(debug=True)