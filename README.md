# apple_music_to_spotify

Hi all this is a script transfers songs from itunes to spotify

For this script you will need to have:

- currently you will need to have windows
- a songs file labelled "library.xml" from your itunes, this can be done by opening itunes --> file --> library -->export playlist -->"library.xml"
  - i have added a sample xml if you don't have itunes   
- a spotify developer account (free) - https://developer.spotify.com/dashboard/login, create and app, create (or take the default) callback url and client id and secret
- access to a regular spotify music account
- a creds/creds.txt folder/file strucuture within your repo, first line of creds/creds.txt should be your spotify dev app client ID, the second line should be your client secret
- a spotify playlist ID (on line 151 of the code) - to obtain this iopen desired spotify playlist and take the string at the end of the URL

You will also need an understanding of the spotify auth code flow, as in this code you will need put your own details in the creds file
- The authorisation is end to end, as such, so long as self.callback_uri and self.playlist_id are correct and self.client_path leads to your client ID and CLient Secret then the code should run end to end for you without need for manual interventions

The mechanics of the code are explained in the body of the code itself in triple quotes marks
