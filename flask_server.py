import json
from pprint import pprint
import secrets
from urllib.parse import urlencode
from flask import Flask, abort, make_response, redirect, render_template, request, session, url_for
import requests
from PIL import Image
from io import BytesIO
import extcolors

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)

SCOPE = 'user-read-currently-playing'
CLIENT_ID = '918bf84807a448e4ab1d399db4f57c8f'
CLIENT_SECRET = '05fea30c83fc4ab8b7f954a534bd1899'
SPOTIFY_ACCESS_TOKEN = ''
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
REDIRECT_URI = 'http://localhost:8080/callback/'


SPOTIFY_GET_CURRENT_TRACK_URL = 'https://api.spotify.com/v1/me/player/currently-playing'


def image_test(current_track_info):
    img = Image.open(requests.get(current_track_info['album_art_link'], stream=True).raw)

    img = img.save("test.jpeg")

    colors, pixelcount = extcolors.extract_from_path("test.jpeg")

    # print(f'\nrgb: {colors[0][0][0]}, {colors[0][0][1]}, {colors[0][0][2]}\n')
    # pprint(colors)
    return colors[0]


def get_current_track(access_token):
    response = requests.get(
        SPOTIFY_GET_CURRENT_TRACK_URL,
        headers =  {
            "Authorization": f"Bearer {access_token}"
        }
    )

    response_json = response.json()

    current_track_info = {
        "id": response_json['item']['id'],
        "album_art_link": response_json['item']['album']['images'][0]['url'],
        "album_art_width": response_json['item']['album']['images'][0]['width'],
        "album_art_height": response_json['item']['album']['images'][0]['height'] 
    }

    current_track_info['rgb'] = image_test(current_track_info)

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

    return get_current_track(session.get('tokens').get('access_token'))


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