import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import *
from tika import parser
import tkinter as tk
import requests
import numpy as np
import os
import sounddevice as sd
import soundfile as sf
import json
import time
import threading
from gtts import gTTS
import pygame

# Define the sampling frequency
fs = 44100

# Define the path to the subfolder
folder_path = 'records'

# Get the list of files in the folder
file_list = os.listdir(folder_path)

# Delete each file in the folder
for file_name in file_list:
    file_path = os.path.join(folder_path, file_name)
    os.remove(file_path)

sound_count = 0

def say_it(txt):
    # set the text you want to convert to speech
    text = txt

    # create a gTTS object
    tts = gTTS(text=text, lang='en')

    # save the audio file as an mp3 format
    tts.save('records/output.mp3')

    # initialize pygame mixer
    pygame.mixer.init()

    # load the audio file
    pygame.mixer.music.load('records/output.mp3')

    # play the audio file
    pygame.mixer.music.play()

    # wait for the audio to finish playing
    while pygame.mixer.music.get_busy():
        continue

    # cleanup pygame mixer
    pygame.mixer.quit()

def get_response(prompt_body):
    url = 'https://experimental.willow.vectara.io/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'customer-id': '',
        'x-api-key': ''
    }
    prompt = prompt_body + " Based on my previous information, give me short description about myself starting with ""You are"". Also give me 5 job titles without descriptions that fit to my CV."
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data).json()
    response_text = response['choices'][0]['message']['content']
    print(response_text)

    GPT_response_box.config(state=tk.NORMAL)
    GPT_response_box.delete('1.0', tk.END)
    GPT_response_box.insert(tk.END, response_text)
    GPT_response_box.config(state=tk.DISABLED)
    # say_it(response_text)

def generate_text(file):
    if file[0] == '{':
        file_name = file[1:-1]
    else:
        file_name = file
    raw = parser.from_file(file_name)
    print(raw['content'])
    get_response(raw['content'])

def path_listbox(event):
    try :
        print(event.data)
        generate_text(event.data)
     
    except OSError as error :
        messagebox.showwarning("Warning", "Drag and drop one CSV file only")

# Define the function that will be called when the "Record" button is pressed
def start_recording():
    global sound_count
    sound_count = sound_count + 1
    # Create a subfolder for the recordings
    folder_name = "records"
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    # Set the recording parameters
    duration = 5  # recording duration in seconds
    sample_rate = 44100  # sampling rate in Hz
    channels = 1  # mono

    # Start the recording
    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)

    # Wait for the recording to finish
    sd.wait()

    # Save the recording to a WAV file
    file_name = os.path.join(folder_name, str(sound_count) + "_recording.wav")
    sf.write(file_name, recording, sample_rate)

    print(f"Recording saved as {file_name}")
    os.system(f"ffmpeg -i {file_name} -vn -ar 44100 -ac 2 -b:a 192k records/" + str(sound_count) + "_recording.mp3")

    url = 'https://experimental.willow.vectara.io/v1/audio/transcriptions'
    headers = {
        'customer-id': '',
        'x-api-key': ''
    }

    data = {
        "model": "whisper-1",
        "messages": [
            {
                "role": "user",
            }
        ]
    }

    with open("records/" + str(sound_count) + "_recording.mp3", "rb") as audio_file:
        files = {'file': ('recording.mp3', audio_file, 'audio/mpeg')}

        response = requests.post(url, headers=headers, data=data, files=files)
        response_json = json.loads(response.content)
        print(response_json['text'])
        get_response(response_json['text'])

window = TkinterDnD.Tk()
window.title('SpotGPT - HR Advisor')
window.geometry('480x600')
frame = tk.Frame(window)
frame.pack()

#Create a Label
label = tk.Label(
    window,
    width = 40,
    height= 1,
    text= "Drag and drop your CV here",
    font= ('Helvetica 18'), bg= '#a0d2eb')
label.pack(ipadx= 50, ipady=50)
label.drop_target_register(DND_FILES)
label.dnd_bind('<<Drop>>', path_listbox)

# toggle_button_state = False

# def toggle_recording():
#     global toggle_button_state, record_time
    
#     if toggle_button_state:
#         toggle_button.config(text="Or record a short voicenote about yourself")
#         toggle_button_state = False
#         record_time = time.time() - record_time
#         print("Recording time: ", record_time)
#         toggle_button_state = True

#         # Start the get_response and say_it functions in separate threads
#         response_thread = threading.Thread(target=get_response)
#         response_thread.start()
#         # say_thread = threading.Thread(target=say_it)
#         # say_thread.start()
        
#     else:
#         start_recording()
#         toggle_button.config(text="Stop")
#         toggle_button_state = True
#         record_time = time.time()

#Create a Button
toggle_button = tk.Button(
    window,
    width = 40,
    height= 1,
    text= "Or record a short voicenote about yourself",
    font= ('Helvetica 18'),
    bg= '#eb8f8f',
    command=start_recording)
toggle_button.pack(ipadx= 50, ipady=50)

# create the text widget
GPT_response_box = tk.Text(window, height=10, width=40, state=tk.DISABLED)

# create the scrollbar widget
scrollbar = tk.Scrollbar(window, command=GPT_response_box.yview)

# configure the text widget to use the scrollbar
GPT_response_box.config(yscrollcommand=scrollbar.set)

# pack the widgets into the window
GPT_response_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

window.mainloop()