from email.mime import base
import json
import math
from pprint import pprint
from re import L
import secrets
import tkinter
from turtle import back
from urllib.parse import urlencode
import webbrowser
from flask import Flask, abort, copy_current_request_context, make_response, redirect, render_template, request, session, url_for
import requests
from PIL import Image, ImageFilter
from io import BytesIO
import extcolors
import os
import threading
import time

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)


# Application settings
DIMMING_FACTOR = .95
COLOR_REJECTION_TOLERANCE = 10
SHADOW_SIZE = 7
SHADOW_STRENGTH = .7
SHADOW_BLUR = 15
ART_SIZE = .7


# DIMMING_FACTOR = .95
# COLOR_REJECTION_TOLERANCE = 10
# SHADOW_SIZE = 15
# SHADOW_STRENGTH = .7
# SHADOW_BLUR = 100
# ART_SIZE = .7

# API-related constants
CLIENT_ID = '918bf84807a448e4ab1d399db4f57c8f'
CLIENT_SECRET = '05fea30c83fc4ab8b7f954a534bd1899'
SCOPE = 'user-read-currently-playing'
SPOTIFY_ACCESS_TOKEN = ''
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_GET_CURRENT_TRACK_URL = 'https://api.spotify.com/v1/me/player/currently-playing'
REDIRECT_URI = 'http://localhost:8080/callback/'

# Dropshadow function taken from https://code.activestate.com/recipes/474116/
def dropShadow( image, background, offset, shadow, 
                border=8, iterations=SHADOW_BLUR):
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
  totalWidth = image.size[0] + abs(offset[0]) + 2*border
  totalHeight = image.size[1] + abs(offset[1]) + 2*border
  back = Image.new('RGB', (totalWidth, totalHeight), background)
  
  # Place the shadow, taking into account the offset from the image
  shadowLeft = border + max(offset[0], 0)
  shadowTop = border + max(offset[1], 0)
  back.paste(shadow, [shadowLeft, shadowTop, shadowLeft + image.size[0], 
    shadowTop + image.size[1]] )
  
  # Apply the filter to blur the edges of the shadow.  Since a small kernel
  # is used, the filter must be applied repeatedly to get a decent blur.
  n = 0
  while n < iterations:
    back = back.filter(ImageFilter.BLUR)
    n += 1
    
  # Paste the input image onto the shadow backdrop  
  imageLeft = border - min(offset[0], 0)
  imageTop = border - min(offset[1], 0)
  back.paste(image, (imageLeft, imageTop))
  
  return back

# Sets desktop wallpaper based on album art of current track
def set_background(current_track_info):
    # Retrieves art from URL
    album = Image.open(requests.get(current_track_info['album_art_link'], stream=True).raw)

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
        if (abs(i[0][0] - i[0][1]) > COLOR_REJECTION_TOLERANCE or  abs(i[0][0] - i[0][2]) > COLOR_REJECTION_TOLERANCE or abs(i[0][2] - i[0][1]) > COLOR_REJECTION_TOLERANCE):
            red = int(i[0][0] * DIMMING_FACTOR)
            green = int(i[0][1] * DIMMING_FACTOR)
            blue = int(i[0][2] * DIMMING_FACTOR)
            break
    
    shadow_r = int(red * SHADOW_STRENGTH)
    shadow_g = int(green * SHADOW_STRENGTH)
    shadow_b = int(blue * SHADOW_STRENGTH)

    # Use tkinter to retrieve monitor dimensions
    tk = tkinter.Tk()
    monitor_width = tk.winfo_screenwidth()
    monitor_height = tk.winfo_screenheight()

    background = Image.new('RGB', (monitor_width, monitor_height), (red, green, blue))

    # Album art size and positioning calculations
    min_dimension = min(monitor_width, monitor_height)
    album_dimension = math.floor(min_dimension * ART_SIZE)
    offset_x = math.floor((monitor_width - album_dimension)/2)
    offset_y = math.floor((monitor_height - album_dimension)/2)
    offset_shadow = math.floor(min_dimension * SHADOW_SIZE/1000)

    album = album.resize((album_dimension, album_dimension), Image.ANTIALIAS)
    album = dropShadow(album, (red, green, blue), (offset_shadow, offset_shadow), (shadow_r, shadow_g, shadow_b))

    output = background.copy()
    output.paste(album, (offset_x, offset_y))
    output.save("test_output.jpeg") 

    # GNOME-desktop specific background setting
    os.system("gsettings set org.gnome.desktop.background picture-uri 'file:///home/iniyuh/code/python/spotifyBackground/test_output.jpeg'")
    os.system("gsettings set org.gnome.desktop.background picture-uri-dark 'file:///home/iniyuh/code/python/spotifyBackground/test_output.jpeg'")

    return colors[0]

def get_current_track():
    response = requests.get(
        SPOTIFY_GET_CURRENT_TRACK_URL,
        headers =  {
            "Authorization": f"Bearer {session.get('tokens').get('access_token')}"
        }
    )

    response_json = response.json()

    current_track_info = {
        "id": response_json['item']['id'],
        "album_art_link": response_json['item']['album']['images'][0]['url'],
        "album_art_width": response_json['item']['album']['images'][0]['width'],
        "album_art_height": response_json['item']['album']['images'][0]['height'] 
    }

    return current_track_info

@app.route('/')
def index():
    return redirect('/login/')

@app.route('/<loginout>/')
def login(loginout):
    if loginout == 'logout':
        payload = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPE,
            'show_dialog': True,
        }
    elif loginout == 'login':
        payload = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPE,
        }
    else:
        abort(404)

    res = make_response(redirect(f'{SPOTIFY_AUTH_URL}/?{urlencode(payload)}'))
    return res


@app.route('/callback/')
def callback():

    @copy_current_request_context
    def looper():
        print(':D')
        previous_track_info = None
        current_track_info = None
        while (True):
            current_track_info = get_current_track()
            if (current_track_info != previous_track_info):
                set_background(current_track_info)
            time.sleep(1)

    error = request.args.get('error')
    code = request.args.get('code')

    # Request tokens with code we obtained
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
    }

    res = requests.post(SPOTIFY_TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET), data=payload)
    res_data = res.json()

    if res_data.get('error') or res.status_code != 200:
        app.logger.error(
            'Failed to receive token: %s',
            res_data.get('error', 'No error information received.'),
        )
        abort(res.status_code)

    session['tokens'] = {
        'access_token': res_data.get('access_token'),
        'refresh_token': res_data.get('refresh_token'),
    }

    threading.Thread(target=looper).start()
    return 'started'

    # return '(:'
    # return get_current_track(session.get('tokens').get('access_token'))


@app.route('/refresh/')
def refresh():
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': session.get('tokens').get('refresh_token'),
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    res = requests.post(
        SPOTIFY_TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET), data=payload, headers=headers
    )
    res_data = res.json()

    session['tokens']['access_token'] = res_data.get('access_token')

    return json.dumps(session['tokens'])

if __name__ == '__main__':
    app.run(host='localhost', port=8080)
