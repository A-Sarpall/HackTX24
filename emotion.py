import cv2
from deepface import DeepFace
from spotifyapi import *
import time
import math

def main():
    # Load face cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Variables
    emotionalvalue = 0.5
    eavg = 0
    total = 0
    emotiondict = {
        "happy": 2,
        "sad" : -1,
        "neutral": -0.15,
        "fear": -1,
        "angry": -1,
        "surprise": 1,
        "disgust": -1
    }
    compareTime = time.time()
    # Start capturing video
    cap = cv2.VideoCapture(0)
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Convert frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Convert grayscale frame to RGB format
        rgb_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)

        # Detect faces in the frame
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            # Extract the face ROI (Region of Interest)
            face_roi = rgb_frame[y:y + h, x:x + w]

        
            # Perform emotion analysis on the face ROI
            result = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)

            # Determine the dominant emotion
            emotion = result[0]['dominant_emotion']

            # Draw rectangle around face and label with predicted emotion
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            # Happy, sad, anger, fear, surprise, neutral
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
                        total = 0
                        emotionalvalue = 0
            
    
        # Display the resulting frame
        cv2.imshow('Real-time Emotion Detection', frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    

    # Release the capture and close all windows
    cap.release()
    cv2.destroyAllWindows()

def updateSong(avg):
    if avg < 0:
        skip_track()
        return True

main()
