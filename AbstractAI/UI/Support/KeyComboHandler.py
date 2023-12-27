import evdev
from evdev import ecodes, categorize
from evdev import KeyEvent as EvdevKeyEvent
from typing import Callable, List, Dict
from dataclasses import dataclass
from PyQt5.QtCore import QTimer
from enum import Enum

# Using evdev's existing key event types, or defining our own if necessary
class KeyEvent(Enum):
	KEY_DOWN = 0
	KEY_UP = 1
	KEY_HOLD = 2
	ANY = 3

@dataclass
class KeyAction:
	device_name: str
	keycode: str
	key_event_type: KeyEvent
	action: Callable

class KeyComboHandler:
	def __init__(self, key_actions: List[KeyAction]):
		self.key_actions_map = {}
		for key_action in key_actions:
			if key_action.device_name not in self.key_actions_map:
				self.key_actions_map[key_action.device_name] = []
			self.key_actions_map[key_action.device_name].append(key_action)
		self.devices = self._discover_devices({ka.device_name for ka in key_actions})
		
		self.timer = QTimer()
		self.timer.timeout.connect(self.check_keys)
		self.timer.start(10)

	def _discover_devices(self, target_device_names: set) -> List[evdev.InputDevice]:
		discovered_devices = []
		for device in [evdev.InputDevice(path) for path in evdev.list_devices()]:
			if device.name in target_device_names:
				discovered_devices.append(device)
				print(f"Found the device: {device.name}")
		if not discovered_devices:
			print("Could not find event numbers for the devices")
			raise RuntimeError("Target devices not found")
		return discovered_devices

	def check_keys(self):
		for dev in self.devices:
			try:
				for event in dev.read():
					if event.type == ecodes.EV_KEY:
						key_event:EvdevKeyEvent = categorize(event)
						print(key_event.keystate)
						for key_action in self.key_actions_map.get(dev.name, []):
							if key_event.keycode == key_action.keycode:
								if key_action.key_event_type == KeyEvent.KEY_DOWN:
									if key_event.keystate == key_event.key_down:
										key_action.action()
								elif key_action.key_event_type == KeyEvent.KEY_UP:
									if key_event.keystate == key_event.key_up:
										key_action.action()
								elif key_action.key_event_type == KeyEvent.KEY_HOLD:
									if key_event.keystate == key_event.key_hold:
										key_action.action()
								elif key_action.key_event_type == KeyEvent.ANY:
									key_action.action()
			except BlockingIOError:
				pass

# Usage example
if __name__ == "__main__":	
	import sys
	from PyQt5.QtWidgets import QApplication
	app = QApplication([])
	
	def on_key_down():
		print("Key down!")

	def on_key_up():
		print("Key up!")
	
	def on_key_hold():
		print("Key hold!")
	
	key_actions = [
		KeyAction(device_name="ThinkPad Extra Buttons", keycode='KEY_PROG1', key_event_type=KeyEvent.KEY_DOWN, action=on_key_down),
		KeyAction(device_name="ThinkPad Extra Buttons", keycode='KEY_PROG1', key_event_type=KeyEvent.KEY_UP, action=on_key_up),
		KeyAction(device_name="ThinkPad Extra Buttons", keycode='KEY_PROG1', key_event_type=KeyEvent.KEY_HOLD, action=on_key_hold),
		KeyAction(device_name="AT Translated Set 2 keyboard", keycode='KEY_CALC', key_event_type=KeyEvent.KEY_DOWN, action=on_key_down),
		KeyAction(device_name="AT Translated Set 2 keyboard", keycode='KEY_CALC', key_event_type=KeyEvent.KEY_UP, action=on_key_up),
		KeyAction(device_name="AT Translated Set 2 keyboard", keycode='KEY_CALC', key_event_type=KeyEvent.KEY_HOLD, action=on_key_hold),
		KeyAction(device_name="Apple, Inc Apple Keyboard", keycode='KEY_F19', key_event_type=KeyEvent.KEY_DOWN, action=on_key_down),
		KeyAction(device_name="Apple, Inc Apple Keyboard", keycode='KEY_F19', key_event_type=KeyEvent.KEY_UP, action=on_key_up),
		KeyAction(device_name="Apple, Inc Apple Keyboard", keycode='KEY_F19', key_event_type=KeyEvent.KEY_HOLD, action=on_key_hold)
	]
	
	key_handler = KeyComboHandler(key_actions=key_actions)
	
	sys.exit(app.exec_())
	