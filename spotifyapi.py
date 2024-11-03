from dotenv import load_dotenv
import os
import base64
import requests
import json
from flask import Flask, request, redirect
import urllib.parse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random

# Load Spotify variables
load_dotenv('client.env')
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = "http://localhost:8888/callback"
scope = "user-modify-playback-state user-read-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))

app = Flask(__name__)
auth_code = None  # Variable to store the authorization code

def get_auth_code_url():
    auth_url = "https://accounts.spotify.com/authorize"
    query_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope
    }
    auth_request_url = f"{auth_url}?{urllib.parse.urlencode(query_params)}"
    return auth_request_url

def get_token(auth_code):
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri
    }
    result = requests.post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    return json_result["access_token"]

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def skip_track():
    try:
        # Check if a song is currently playing
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            sp.next_track()
            print("Skipped the current song.")
        else:
            print("No song is currently playing.")
    except spotipy.exceptions.SpotifyException as e:
        print("Error:", e)

def pause_track():
    try:
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            sp.pause_playback()
            print("Paused the current song.")
        else:
            sp.start_playback()
            print("Resumed the current song.")
    except spotipy.exceptions.SpotifyException as e:
        print("Error:", e)

def queue_track(uri):
    try:
        sp.add_to_queue(uri)
        print(f"added {uri} to queue")
    except spotipy.exceptions.SpotifyException as e:
        print("Error:", e)

def add_playlist_to_queue(playlist_uri):
    try:
        # Get tracks from the playlist
        results = sp.playlist_tracks(playlist_uri)
        tracks = results['items']

        random.shuffle(tracks)
        
        # Queue each track from the playlist
        for item in tracks:
            track_uri = item['track']['uri']  # Extract track URI
            queue_track(track_uri)  # Queue the track
            
    except spotipy.exceptions.SpotifyException as e:
        print("Error adding playlist to queue:", e)

def queue_length():
    return len(sp.queue())

#def recommend():
#    sp.recommendations(seed_artists=sp.currently_playing, seed_genres=None, seed_tracks=None, limit=20, country=None, **kwargs)

@app.route("/")
def authorize():
    auth_request_url = get_auth_code_url()
    return redirect(auth_request_url)

@app.route("/callback")
def callback():
    global auth_code
    auth_code = request.args.get("code")
    return "Authorization code received! You can close this tab."
