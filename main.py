import subprocess
import requests
from PIL import Image, ImageFilter
import extcolors
from AppKit import NSScreen
import math
import os
import time
import atexit
import sys
import signal
import os

# Image manipulation settings
DIMMING_FACTOR = .95
COLOR_REJECTION_TOLERANCE = 10
SHADOW_SIZE = 7
SHADOW_STRENGTH = .7
SHADOW_BLUR = 15
ART_SIZE = .7

def add_drop_shadow(image, background, offset, shadow, border=8, iterations=SHADOW_BLUR):
    """
    Add a gaussian blur drop shadow to an image.

    image       - The image to overlay on top of the shadow.
    offset      - Offset of the shadow from the image as an (x,y) tuple.  Can be
                  positive or negative.
    background  - Background colour behind the image.
    shadow      - Shadow colour (darkness).
    border      - Width of the border around the image.  This must be wide
                  enough to account for the blurring of the shadow.
    iterations  - Number of times to apply the filter.  More iterations
                  produce a more blurred shadow, but increase processing time.
    """

    # Create the backdrop image -- a box in the background colour with a
    # shadow on it.
    total_width = image.size[0] + abs(offset[0]) + 2 * border
    total_height = image.size[1] + abs(offset[1]) + 2 * border
    back = Image.new('RGB', (total_width, total_height), background)

    # Place the shadow, taking into account the offset from the image
    shadow_left = border + max(offset[0], 0)
    shadow_top = border + max(offset[1], 0)
    back.paste(shadow, [shadow_left, shadow_top, shadow_left + image.size[0],
                        shadow_top + image.size[1]])

    # Apply the filter to blur the edges of the shadow.  Since a small kernel
    # is used, the filter must be applied repeatedly to get a decent blur.
    n = 0
    while n < iterations:
        back = back.filter(ImageFilter.BLUR)
        n += 1

    # Paste the input image onto the shadow backdrop
    image_left = border - min(offset[0], 0)
    image_top = border - min(offset[1], 0)
    back.paste(image, (image_left, image_top))

    return back

def create_background(art_link, filepath):
    # Retrieves art from URL
    album = Image.open(requests.get(art_link, stream=True).raw)

    # Uses extcolors library to extract most predominant colors
    colors = extcolors.extract_from_image(album)[0]

    red = colors[0][0][0]
    green = colors[0][0][1]
    blue = colors[0][0][2]
    shadow_r = 0
    shadow_g = 0
    shadow_b = 0

    for i in colors:
        # Filters out neutrals for background color selection
        if (abs(i[0][0] - i[0][1]) > COLOR_REJECTION_TOLERANCE or abs(
                i[0][0] - i[0][2]) > COLOR_REJECTION_TOLERANCE or abs(i[0][2] - i[0][1]) > COLOR_REJECTION_TOLERANCE):
            red = int(i[0][0] * DIMMING_FACTOR)
            green = int(i[0][1] * DIMMING_FACTOR)
            blue = int(i[0][2] * DIMMING_FACTOR)
            break

    shadow_r = int(red * SHADOW_STRENGTH)
    shadow_g = int(green * SHADOW_STRENGTH)
    shadow_b = int(blue * SHADOW_STRENGTH)

    # Use AppKit to retrieve monitor dimensions
    monitor_width, monitor_height = int(NSScreen.mainScreen().frame()[1][0]), int(NSScreen.mainScreen().frame()[1][1])

    background = Image.new('RGB', (monitor_width, monitor_height), (red, green, blue))

    # Album art size and positioning calculations
    min_dimension = min(monitor_width, monitor_height)
    album_dimension = math.floor(min_dimension * ART_SIZE)
    offset_x = math.floor((monitor_width - album_dimension) / 2)
    offset_y = math.floor((monitor_height - album_dimension) / 2)
    offset_shadow = math.floor(min_dimension * SHADOW_SIZE / 1000)

    album = album.resize((album_dimension, album_dimension), Image.LANCZOS)
    album = add_drop_shadow(album, (red, green, blue), (offset_shadow, offset_shadow), (shadow_r, shadow_g, shadow_b))

    output = background.copy()
    output.paste(album, (offset_x, offset_y))
    output.save(filepath)

def set_unique_wallpaper_and_restart_dock(current_track):
    # Create a filename based on track title and artist
    filename = f'{current_track["Track Title"]}_{current_track["Track Artist"]}.jpeg'
    # filename = f'{current_track.splitlines()[0]} {current_track.splitlines()[1]}.jpeg'
    source_image_url = current_track["Artwork URL"]

    # Define the destination directory
    dest_directory = os.path.expanduser("~/Pictures/spotipapers/")

    # Create the directory if it doesn't exist
    os.makedirs(dest_directory, exist_ok=True)

    # Define the destination path
    dest_image_path = os.path.join(dest_directory, filename)

    # Check if the wallpaper already exists
    if not os.path.exists(dest_image_path):
        create_background(source_image_url, dest_image_path)

    os.system(
        f'/usr/libexec/PlistBuddy -c "set AllSpacesAndDisplays:Desktop:Content:Choices:0:Files:0:relative file:///{dest_image_path}" ~/Library/Application\ Support/com.apple.wallpaper/Store/Index.plist && \
        killall WallpaperAgent'
    )


def start_applescript():
    subprocess.Popen(["open", "spotify_monitor.app"])

def stop_applescript():
    subprocess.run(["killall", "spotify_monitor"])

def read_current_track():
    art_url_file_path = os.path.expanduser("~/Pictures/spotipapers/current_spotify_track_info.txt")
    track_info = {
        'Track Title': None,
        'Track Artist': None,
        'Artwork URL': None
    }
    if os.path.exists(art_url_file_path):
        with open(art_url_file_path, "r") as file:
            for line in file:
                if line.startswith('Track Title:'):
                    track_info['Track Title'] = line[len('Track Title:'):].strip()
                elif line.startswith('Track Artist:'):
                    track_info['Track Artist'] = line[len('Track Artist:'):].strip()
                elif line.startswith('Artwork URL:'):
                    track_info['Artwork URL'] = line[len('Artwork URL:'):].strip()
        return track_info
    return None

def stop_applescript_app():
    """Stop the AppleScript application using killall."""
    print("Stopping the AppleScript application: spotify_monitor")
    os.system('pkill -9 -f spotify_monitor')

def exit_handler():
    """Atexit handler to stop the AppleScript app."""
    print("Executing atexit handler.")
    stop_applescript_app()

def signal_handler(sig, frame):
    """Signal handler to stop the AppleScript app and exit gracefully."""
    print(f"Received signal {sig}, exiting gracefully...")
    stop_applescript_app()
    sys.exit(0)





























import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QThread


class WallpaperChangerThread(QThread):
    def __init__(self):
        super().__init__()
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        start_applescript()
        previous_track = {'Artwork URL': ""}
        while self._running:
            current_track = read_current_track()
            if current_track["Artwork URL"] != previous_track["Artwork URL"] and current_track["Artwork URL"] != "missing value":
                set_unique_wallpaper_and_restart_dock(current_track)
                previous_track = current_track
            time.sleep(5)

class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.setToolTip('System Tray Utility')
        self.menu = QMenu(parent)
        self.init_menu()
        self.setContextMenu(self.menu)

    def init_menu(self):
        start_action = QAction("Start", self)
        start_action.triggered.connect(self.start_action)
        self.menu.addAction(start_action)

        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.stop_action)
        self.menu.addAction(stop_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.settings_action)
        self.menu.addAction(settings_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(sys.exit)
        self.menu.addAction(exit_action)

    # def start_action(self):
    #     QMessageBox.information(None, 'Action', 'Start the application!')
    #     self.worker = WallpaperChangerThread()
    #     self.worker.start()

    def start_action(self):
        # This check is to ensure that the worker thread isn't already running
        if hasattr(self, 'worker') and self.worker.isRunning():
            print("The application is already running.")
        else:
            self.worker = WallpaperChangerThread()
            self.worker.start()

    def stop_action(self):
        QMessageBox.information(None, 'Action', 'Stop the application!')
        stop_applescript()
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            QMessageBox.information(None, 'Action', 'Stopped the application!')

    def settings_action(self):
        QMessageBox.information(None, 'Settings', 'Adjust settings here!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep the app running without a main window
    atexit.register(exit_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    tray_icon = SystemTrayApp(QIcon("icon.png"))
    tray_icon.show()

    sys.exit(app.exec())
