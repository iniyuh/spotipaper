from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'packages': ['PyQt6'],
    'argv_emulation': False,
    'iconfile': 'app_icon.icns',  # macOS icon file
    'plist': {
        'LSUIElement': True,  # This key tells macOS to not show the app icon in the Dock
    },
}

setup(
    app=APP,
    name="spotipaper",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
