from http.server import BaseHTTPRequestHandler
from pprint import pprint
from urllib import response
from urllib import parse
import requests

SPOTIFY_GET_CURRENT_TRACK_URL = 'https://api.spotify.com/v1/me/player/currently-playing'

SCOPE = 'user-read-currently-playing'

CLIENT_ID = '918bf84807a448e4ab1d399db4f57c8f'
CLIENT_SECRET = '05fea30c83fc4ab8b7f954a534bd1899'

SPOTIFY_ACCESS_TOKEN = 'BQC0WcWbaPV6jBTvExKvNn_FtJ4RgntGfouumiyel2CUnVXSRFhSCCFUpNQSvU0qn30iYKwTz7x43J7JZbIHXC69zcOdtk-fBGNw92LWgkz6mHAZUitTSvRrhEUSaNI7dK98C0wP4J6umyZfyuXkDX-zVWvX'
SPOTIFY_ACCESS_TOKEN = ''



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

    return current_track_info

def main():
    current_track_info = get_current_track(
        SPOTIFY_ACCESS_TOKEN
    )

    pprint(current_track_info, indent=4)

if __name__ == '__main__':
    main()