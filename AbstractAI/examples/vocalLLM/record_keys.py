#This is a example script that uses the evdev library to record key presses
#and then send them to the server for transcription.

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
import math
import time
import argparse
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QMouseEvent

from AbstractAI.Helpers.AudioRecorder import AudioRecorder, AudioSegment

import evdev
from evdev import categorize, ecodes

import pyperclip
import pyautogui
pyautogui.FAILSAFE = False

class Application(QMainWindow):
    def __init__(self):
        super().__init__()
        
        from AbstractAI.Remote.client import System
        self.System = System
        
        self.diam = 60  # Diameter of the dot
        # Window attributes
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.diam, self.diam)
        self.dot_color = QColor(255, 0, 0)  # Initial color for not recording
        self.setWindowFlags(self.windowFlags() | Qt.X11BypassWindowManagerHint)

        self.prev_result = None
        self.recorder = AudioRecorder()
        
        # Initialize multiple devices
        self.devices = []
        
        for device in [evdev.InputDevice(path) for path in evdev.list_devices()]:
            print(f"Path: {device.path}, Name: {device.name}, Phys: {device.phys}, Uniq: {device.uniq}, Info: {device.info}")
            
            def add_device(device):
                self.devices.append(device)
                print(f"Found the device: {device.name}")
            def conditional_add(device, name):
                if device.name == name:
                    add_device(device)
            
            conditional_add(device, "ThinkPad Extra Buttons")
            conditional_add(device, "AT Translated Set 2 keyboard")
            if device.name == "Apple, Inc Apple Keyboard" and device.phys.endswith("input0"):
                add_device(device)
        
        if not self.devices:
            print("Could not find event numbers for the devices")
            sys.exit(1)
        print(evdev.list_devices())
            
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_button)
        self.timer.timeout.connect(self.update_color)
        self.timer.start(10)  # Check every 10ms

        self.is_recording = False
        self.is_processing = False
        self.was_processing = False
        self.positionOnPrimaryMonitor()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(self.dot_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(-self.diam/2), int(-self.diam/2), self.diam, self.diam)
    
    def positionOnPrimaryMonitor(self):
        primaryMonitor = QDesktopWidget().primaryScreen()
        screenGeometry = QDesktopWidget().screenGeometry(primaryMonitor)
        self.move(screenGeometry.topLeft())
        
    def update_color(self):
        if self.is_processing:
            self.dot_color = QColor(100, 100, 255)
        elif self.is_recording:
            self.dot_color = QColor(int(math.sin(datetime.now().timestamp() * 3) * 30 + 225), 0, 0)
        else:
            self.dot_color = QColor(0, 255, 0)
        self.update()
    
    def check_button(self):
        self.positionOnPrimaryMonitor()
        for dev in self.devices:
            try:
                for event in dev.read():
                    if event.type == ecodes.EV_KEY:
                        key_event = categorize(event)
                        if key_event.keycode in ['KEY_PROG1', 'KEY_F19', 'KEY_CALC']:
                            if key_event.keystate == key_event.key_down:
                                print("==========================")
                                self.toggle_recording()
            except BlockingIOError:
                pass

    def process_audio(self, audio_segment: AudioSegment):
        # Your code here
        self.is_processing = True
        result = self.System.transcribe_str(audio_segment)
        
        # remove spaces and new lines at the beginning and end of the string:
        result = result.strip()
        self.prev_result = result
        
        #pyautogui.write(result)Blah blah blah blah blah.
        
        # pyautogui.typewrite(result, interval=0.0001)
        
        current_clipboard = pyperclip.paste()
        pyperclip.copy(result)
        
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        pyperclip.copy(current_clipboard)
        
        self.is_processing = False
        
    def toggle_recording(self):
        if self.is_processing:
            return
        
        if self.is_recording:
            audio_segment = self.recorder.stop_recording()
            
            #Process the audio on another thread. without waiting. eg: self.process_audio(file_name) as a thread:
            from threading import Thread
            Thread(target=self.process_audio, args=(audio_segment,)).start()
            
        else:
            print("\n\n\n\n\n")
            self.recorder.start_recording()
        self.is_recording = not self.is_recording
    
    def mousePressEvent(self, event: QMouseEvent):
        if self.is_point_in_circle(event.pos()):
            if event.button() == Qt.LeftButton:
                self.toggle_recording()
            elif event.button() == Qt.RightButton and self.prev_result is not None:
                pyperclip.copy(self.prev_result)

    def is_point_in_circle(self, point: QPoint):
        circle_center = QPoint(0, 0)
        distance_to_center = (point - circle_center).manhattanLength()
        return distance_to_center <= self.diam / 2

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Application()
    window.show()
    sys.exit(app.exec_())