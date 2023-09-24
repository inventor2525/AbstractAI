#This is a example script (a utility) that uses the evdev library to
#record key presses and then send them to the server for transcription
#and then paste the transcription into the active window.

#Currently, this script only works on Linux, and only with the ThinkPad Extra Buttons,
#but it could be modified to work with other keyboards and operating systems.

#To use this script, you must first install the evdev library:
#pip install evdev

#Then, you must find the event number for the key you want to use.
#To do this, first add yourself to the input group by running the following command:
#sudo usermod -a -G input <username>

#Then run 'evtest' and, select a group of keys using the on screen
#instructions, and press the key you want to use to get its keycode.

#Finally, run this script with the event number and the server's IP
#address and port number of your whisper server. See /examples/vocalLLM/server.py

#It will then toggle recording when you press the key, and send the recording
#to the server for transcription when you release the key, and then paste the
#transcription into the active window.

import sys
import argparse
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor
from AbstractAI.Helpers.AudioRecorder import AudioRecorder
from AbstractAI.SpeechToText.STT_Client import STT_Client
import evdev
from evdev import InputDevice, categorize, ecodes
import pyperclip
import pyautogui
from pydub.exceptions import CouldntDecodeError

import subprocess
import re
import os

def capture_partial_output(command, timeout=1):
	import pty
	import subprocess
	import select
	
	master, slave = pty.openpty()
	proc = subprocess.Popen(command, stdout=slave, stderr=slave, text=True)
	os.close(slave)
	output_lines = []

	try:
		while True:
			ready, _, _ = select.select([master], [], [], timeout)
			if ready:
				line = os.read(master, 512).decode('utf-8')
				if not line:
					break
				output_lines.append(line)
			else:
				# timeout
				break
	finally:
		os.close(master)
		proc.kill()

	return ''.join(output_lines)
    
class Application(QMainWindow):
    def __init__(self, host, port):
        super().__init__()

        self.diam = 20  # Diameter of the dot
        # Window attributes
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.diam, self.diam)
        self.dot_color = QColor(255, 0, 0)  # Initial color for not recording

        self.host = host
        self.port = port
        self.recorder = AudioRecorder()
        self.stt = STT_Client(host, port)
        
        output = capture_partial_output(["evtest"])
        result = re.search('/dev/input/event(\d+):.*ThinkPad Extra Buttons', output)
        if result:
            event_number = result.group(1)
            self.dev = InputDevice(f"/dev/input/event{event_number}")
        else:
            print("Could not find event number for ThinkPad Extra Buttons")
            sys.exit(1)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_button)
        self.timer.start(10)  # Check every 10ms

        self.is_recording = False
        
        self.move(0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(self.dot_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(-self.diam/2), int(-self.diam/2), self.diam, self.diam)

    def check_button(self):
        try:
            for event in self.dev.read():
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    if key_event.keycode == 'KEY_PROG1':
                        if key_event.keystate == key_event.key_down:
                            self.toggle_recording()
        except BlockingIOError:
            pass

    def toggle_recording(self):
        if self.is_recording:
            self.dot_color = QColor(255, 0, 0)
            file_name = 'temp.mp3'
            audio_segment = self.recorder.stop_recording()
            audio_segment.export(file_name, format="mp3")
            result = self.stt.transcribe_str(file_name)
            # remove spaces and new lines at the beginning and end of the string:
            result = result.strip()
            
            #pyautogui.write(result)
            
            #pyautogui.typewrite(result, interval=0.0001)
            
            pyperclip.copy(result)
            pyautogui.hotkey('ctrl', 'v')
        else:
            self.dot_color = QColor(0, 255, 0)
            self.recorder.start_recording()
        self.is_recording = not self.is_recording
        self.update()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Remote Speech-to-Text Client with ThinkPad Button Integration')
    parser.add_argument('host', type=str, help='The server\'s IP address or hostname (e.g., \'localhost\' or \'0.0.0.0\').')
    parser.add_argument('port', type=int, help='The port number on which the server is running (e.g., 8000).', default=8000)
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = Application(args.host, args.port)
    window.show()
    sys.exit(app.exec_())