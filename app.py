from flask import Flask, Response, render_template  # Import render_template
import cv2
from deepface import DeepFace
from spotifyapi import *
import time
from flask_socketio import SocketIO, emit
from threading import Thread
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv('client.env')
API_KEY = os.getenv("API_KEY")
genai.configure(api_key=os.environ["API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")
app = Flask(__name__)
evalue = 0
socketio = SocketIO(app)
currentSong = 0


def generate_frames():
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    # Variables
    emotionalvalue = 1
    eavg = 0
    total = 0
    emotiondict = {
        "happy": 2,
        "sad" : -1,
        "neutral": -0.15,
        "fear": -1,
        "angry": -1,
        "surprise": 1,
        "disgust": -1.5,
        None: 0
    }
    compareTime = time.time()


    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
        faces = face_cascade.detectMultiScale(gray_frame, 1.1, 4)
        emotion = None

        for (x, y, w, h) in faces:
            face_roi = rgb_frame[y:y + h, x:x + w]
            result = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)
            emotion = result[0]['dominant_emotion']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        # Happy, sad, anger, fear, surprise, neutral

        if emotion != None:
            emotionalvalue += emotiondict[emotion]
            total += 1
            eavg = emotionalvalue / total
            print(eavg)

            if (time.time() - compareTime) >= 8.0:
                    print("thinking")
                    total -= 0.5
                    emotionalvalue -= 0.5
                    if updateSong(eavg):
                        compareTime = time.time()
                        total = 1
                        emotionalvalue = 1
                        

    cap.release()

@socketio.on('user_logged_in')  # Listen for user login event
def handle_user_logged_in(data):
    access_token = data['token']  # Retrieve the access token
    print(f"User logged in with token: {access_token}")

def video_capture():
    global frame_generator
    frame_generator = generate_frames()

@app.route('/')
def index():  # Add this route to serve the HTML page
    return render_template('index.html')  # Render the index.html template

@app.route('/video_feed')
def video_feed():
    return Response(frame_generator, mimetype='multipart/x-mixed-replace; boundary=frame')
    

@socketio.on('skip')  # Listen for skip event from the client
def handle_skip():
    skip_track()  # Call the function to skip the track
    socketio.emit('status', {'message': 'Track skipped by user.'})  # Emit status message

@socketio.on('song_playing')  # Event to indicate a song is playing
def song_playing():
    global is_playing
    is_playing = True  # Set the flag to indicate a song is playing
    print("song now playing")

@socketio.on('song_stopped')  # Event to indicate a song has stopped
def song_stopped():
    global is_playing
    is_playing = False  # Set the flag to indicate playback has stopped

def updateSong(avg):
    global currentSong  # Add this to access the global variable
    if avg < 0:
        # Make sure we don't go out of bounds of the URI list
        if currentSong == 0:
            add_playlist_to_queue("spotify:playlist:37i9dQZEVXbLp5XoPON0wI")
        if currentSong < queue_length() - 1:
            currentSong += 1
        print(queue_length())
        skip_track()
        # Emit the URI as a string in a proper data structure
        
        
        #socketio.emit('play_next_song', {'uri': URI[currentSong]})
        #socketio.emit('status', {'message': 'Track skipped due to negative emotion average.'})
        return True

if __name__ == "__main__":
    video_capture_thread = Thread(target=video_capture)
    video_capture_thread.start()
    socketio.run(app, debug=True)  # Use socketio.run instead of app.run
