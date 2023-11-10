from setuptools import setup

setup(
	name='AbstractAI',
	version='0.0.1',
	author='Charlie Angela Mehlenbeck',
	author_email='charlie_inventor2003@yahoo.com',
	packages=['AbstractAI'],
	py_modules=[],
	scripts=[],
	url='https://github.com/inventor2525/AbstractAI',
	license='LICENSE',
	description='A simple library to abstract various ML models.',
	long_description=open('README.md').read(),
	install_requires=[
		'numpy',
		'torch>=2.0.1',
		'numexpr>=2.8.4',
		'transformers',
		'bitsandbytes',
		'einops',
		'accelerate',
		'xformers',
		'scipy',
		'sentencepiece',
		'openai-whisper',
		'datasets',
		'soundfile',
		'nltk',
		'PyQt5',
		'sounddevice',
		'pydub',
		'evdev',
		'pyperclip',
		'pyautogui'
	],
	python_requires='~=3.10'
)
