import numpy as np
class AMMS:
	def __init__(self):
		self.values = []
	
	def add(self, value):
		self.values.append(value)
	
	def current(self):
		return self.values[-1]
	
	def average(self):
		return np.mean(self.values)
	
	def min(self):
		return np.min(self.values)
	
	def max(self):
		return np.max(self.values)
	
	def std(self):
		return np.std(self.values)
	
	def __str__(self):
		return f"current={self.current():.2f} average={self.average():.2f} min={self.min():.2f} max={self.max():.2f} std={self.std():.2f}"
