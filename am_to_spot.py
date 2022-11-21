import requests
import base64
import pandas as pd
import lxml.etree as ET
import urllib.parse
import json
from urllib.parse import urlencode
import webbrowser
import uiautomation as auto
import time
import platform
import os
import win32com.client as pywin32

system = platform.system()


'''This section has some base arguments custom functions/decorators that are generic and can be applied to other codes'''

def song_check_loop(func):
    def wrapper(self):
        for song, artist in track_list.items():
            func(self, song, artist, search_song_auth_code)
    return wrapper
def song_add_loop(func):
    def wrapper(self):
        for id in self.song_ids:
            func(self, id, add_song_auth_code)
    return wrapper

'''MAIN CLASSES'''

class AppleMusicSongList():
    def __init__(self):
        self.song_list = []
        self.artist_list = []
        self.album_list = []

    '''THe XML itunes library data is parsed, song data is within a dict of a dict of a dict'''
    def obtain_track_detail_tags(self):
        xml = "library.xml"
        tree = ET.parse(xml)
        root = tree.getroot()
        self.track_details_tags = root.findall("dict")[0].findall("dict")[0].findall("dict") #each layer just happens to nbe called "dict" this is eqv to saying "1st dict/1st dict/{all things that are called dict"

    '''Within the final dicts, songs are characterised as having "Apple Music AAC audio file" text in a string tag'''
    def extract_songs(self):
        x=0
        for track_details_tag in self.track_details_tags:
            music_check = track_details_tag.findall("string")
            for check in music_check:
                if check.text == "Apple Music AAC audio file":
                    track_details = track_details_tag.xpath('.//key | .//integer | .//string | .//date | .//true')
                    for n, track_detail in enumerate(track_details):
                        if track_detail.text == "Name":self.song_list.append(track_details[n+1].text)
                        if track_detail.text == "Artist":self.artist_list.append(track_details[n+1].text)
                        if track_detail.text == "Album":self.album_list.append(track_details[n+1].text)
            x += 1

    '''Further Processing to clean up song names'''
    def clean_songs_list(self):
        self.song_list = [song.split("(")[0]for song in self.song_list]
        self.artist_list = [artist.replace("&", " ") for artist in self.artist_list]

    '''Converting a List of song names, artists and album names into a dataframe'''
    def df_creation_control(self):
        tracks_df = pd.DataFrame({"Song":self.song_list,"Artist":self.artist_list,"Album":self.album_list})
        tracks_df.to_csv("song_list.csv", index=False)
        print(f"\nSong Table:\n{tracks_df.head()}")

class Authorisations():
    def __init__(self):
        self.client_path = "creds/creds.txt"
        f = open(self.client_path, "r")
        lines = f.readlines()
        self.CLIENT_ID = lines[0].strip()
        self.CLIENT_SECRET = lines[1].strip()
        self.AUTH_URL = 'https://accounts.spotify.com/api/token'
        self.TOKEN_URL = 'https://accounts.spotify.com/api/token'
        self.callback_uri = 'https://oauth.pstmn.io/v1/browser-callback'
        self.chrome_path = "C:/ProgramData\Microsoft\Windows\Start Menu\Programs\Google Chrome.lnk"
        # self.chrome_path = shell.CreateShortCut(self.chrome_path).Targetpath
        if system == "Linux":
            print([os.path.realpath(item) for item in os.listdir('.')])
        elif system == "Windows":
            shell = pywin32.Dispatch("WScript.Shell")
            self.chrome_path = shell.CreateShortCut(self.chrome_path).Targetpath
            self.chrome_path = self.chrome_path.replace('\\','/') + " %s"
            print(self.chrome_path)

    '''POST request for client details, this is a low level API token that allows the searching of songs on spotify'''
    def search_song_auth(self):

        search_request = requests.post(self.AUTH_URL, {
            'grant_type': 'client_credentials',
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
        })

        '''convert the response to JSON in order to access the token'''
        search_request = search_request.json()
        search_access_token = search_request['access_token']
        return search_access_token

    '''This method Gets the authorizations for adding song, this is an auth 2.0 auth flow meaning:
     - first an auth code is retrieved from a browser URL using a get request
     - that auth code is then posted to an API token endpoint, a token code in then returned
     - this token can then be used as authorisation to post songs to the spotify playlist of your choice'''

    '''As the code for the access token retrieval is actually in a callback url this tool allows us to read a url in a google chrome tab. 
    This is handy as it means we don't have to manually retrieve the url from the browser, the code does it for us'''
    def add_song_auth(self):
        auth_code_headers = {
            "Content-Type": "application/json",
            'client_id': self.CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': self.callback_uri,
            'scope': "playlist-modify-public playlist-read-private playlist-modify-private",
        }

        # chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"
        webbrowser.get(self.chrome_path).open("https://accounts.spotify.com/authorize?" + urlencode(auth_code_headers))

        time.sleep(1.5)
        control = auto.GetFocusedControl()
        controlList = []
        while control:
            controlList.insert(0, control)
            control = control.GetParentControl()
        control = controlList[0 if len(controlList) == 1 else 1]
        address_control = auto.FindControl(control, lambda c, d:
        isinstance(c, auto.EditControl))

        auth_url = address_control.GetValuePattern().Value
        auth_code = auth_url.split("code=")[1]

        '''Once we have the code it is time to post it to the API endpoint in order to retrieve the the access token
         with modify scopes'''

        authorization = base64.urlsafe_b64encode(
            (self.CLIENT_ID + ':' + self.CLIENT_SECRET).encode()).decode()  # url safe makes the difference

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {authorization}'
        }
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.callback_uri
        }

        add_song_access_token = requests.post(url=self.TOKEN_URL, data=data, headers=headers)
        add_song_access_token = add_song_access_token.json()
        return add_song_access_token["access_token"]

class SpotifyClient():
    def __init__(self):
        self.search_endpoint = "https://api.spotify.com/v1/search?"
        self.playlist_endpoint = "https://api.spotify.com/v1/playlists"
        self.playlist_id = "0PQqePki0O3ct1gs5iptjM" #go to desired playlist in spotify, this is the string at the end of the url
        self.song_ids = []
        self.exception = []


    '''This method uses the search access token to search for song in spotify from out itunes, if it cannot find the
        songs. If it cannot find one it returns it to the exception list which can be viewed at the end if the code'''

    @song_check_loop
    def search_songs(self, song, artist, search_song_auth_code):
        query = urllib.parse.quote(f'{artist} {song}')
        url = f'{self.search_endpoint}q={query}&type=track'

        response = requests.get(
            url,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(search_song_auth_code)
            }
        )
        response_json = response.json()

        with open('data.json', 'w') as f:
            json.dump(response_json, f)
        results = response_json['tracks']['items']
        if results:
            # lets assumed the first track in the list is the song we want
            self.song_ids.append(results[0]['id'])
        else:
            print(f'Exception: No song found for {artist} - {song}')
            self.exception.append(f"{song} - {artist}")

    '''This method uses the add song access token to add songs to a playlist of your choice, defined by "self.playlist_id"'''

    @song_add_loop
    def add_song_to_spotify(self, id, add_song_auth_code):
        url = f'{self.playlist_endpoint}/{self.playlist_id}/tracks?uris=spotify%3Atrack%3A{id}'
        response = requests.post(
            url,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {add_song_auth_code}'
            },
        )
        if response.status_code != 201:
            print(response.status_code, response.reason, response.url)
        return response.ok

    def icing(self):
        print(self.exception)

'''RUN'''

print("\n\n1 - Parsing Apple Library - Preparing song data...")

apple_music_class_object = AppleMusicSongList()
apple_music_class_object.obtain_track_detail_tags()
apple_music_class_object.extract_songs()
apple_music_class_object.clean_songs_list()
apple_music_class_object.df_creation_control()


print("\n 2 - Setting up spotify server authorisations...")

auth_class_object = Authorisations()
search_song_auth_code = auth_class_object.search_song_auth()
add_song_auth_code = auth_class_object.add_song_auth()

print("\n 3 - Adding songs to Spotify!...")

song_list = pd.read_csv("song_list.csv")
track_list = dict(zip(song_list["Song"], song_list["Artist"]))


spotify_class_object = SpotifyClient()
spotify_class_object.search_songs()
spotify_class_object.add_song_to_spotify()
spotify_class_object.icing()

print("\n 4 - Transfer Done - Thank you for using my script")