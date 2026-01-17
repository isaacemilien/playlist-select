#!/usr/bin/env python3
import json
import subprocess
import sys
import termios
import tty
import requests

def populate_playlist_interface(raw_dump, url, title):
    playlist_interface = []

    if title not in raw_dump["entries"][0]:
        title = url

    for entry in raw_dump["entries"]:
        playlist_interface.append({'url': entry[url], 'title': entry[title]})

    return playlist_interface

def get_playlist_data(url, items):
    result = subprocess.run(
        ['yt-dlp', '-J', '--flat-playlist', '--playlist-items', '1-' + str(items), url],
        capture_output=True,
        text=True,
        check=True
    )

    raw_dump = json.loads(result.stdout)

    return populate_playlist_interface(raw_dump, 'url', 'title')

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)

        if ch == '\x1b':
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def draw(playlist_idx, playlist, playlist_len, selection_char = ">"):
    """Prints all entries in playlist, takes given index and prepends ">" character to signify current selection

    Args: 
        playlist_idx: The playlist index to prepend selection character to.
        playlist: Dictionary representing current playlist.
        playlist_len: Number representing length of playlist.
        selection_char: Character to prepend to currently selected element
    """
    print('\033[2J\033[H', end='')

    low = playlist_idx - (playlist_idx % 10) 
    high = playlist_len if low + 10 > playlist_len else low + 10

    for i in range(low, high):
        pref = selection_char if i == playlist_idx else " "
        print(pref, str(i + 1) + ".",playlist[i]["title"] )

def select(playlist, playlist_idx, playlist_len, default_mpv_command):
    playlists = []
    playlists.append({
        "playlist_data": playlist, 
        "playlist_idx": playlist_idx})

    draw(playlist_idx, playlist, playlist_len)
    
    while True: 
        key = get_key()

        match key:
            case 'q':
                sys.exit(0) 
            case 'p':
                print("\n\nExit with playlist url: ", playlist[playlist_idx]["url"])
                sys.exit(0) 
            case 'j' | '\033[B':
                playlist_idx += 1
                new_selection = True
            case 'k' | '\033[A':
                playlist_idx -= 1
                new_selection = True
            case 'J':
                playlist_idx += 10
                new_selection = True
            case 'K':
                playlist_idx -= 10
                new_selection = True
            case 'l':
                # FIX INDENT ON PLAYLISTS
                # FIX CRASH ON NO TITLE, SHOULD JUST DEFAULT TO URL OR SOMETHING
                # ADD LITTLE PRINT AT TOP OF PLAYLISTS FOR THE CURRENT PLAYLISTS SO THAT IS SHOWS INDENTATION LEVEL

                # add in queue here to represent playlist hierarchy
                playlists[-1]["playlist_idx"] = playlist_idx

                playlists.append({
                    "playlist_data": get_playlist_data(playlist[playlist_idx]["url"], playlist_items), 
                    "playlist_idx": playlist_idx})

                playlist = playlists[-1]["playlist_data"]
                playlist_idx = 0
                new_selection = True
            case 'h':
                playlists.pop()
                playlist = playlists[-1]["playlist_data"]
                playlist_idx = playlists[-1]["playlist_idx"]
                new_selection = True
            case '\r':
                draw(playlist_idx, playlist, playlist_len, "    >")
                subprocess.run(default_mpv_command + [playlist[playlist_idx]["url"]])
                new_selection = True
            case 'v':
                draw(playlist_idx, playlist, playlist_len, "    >")
                subprocess.run(default_mpv_command + [playlist[playlist_idx]["url"], '-ytdl-format=299+bestaudio'])
                new_selection = True

        if new_selection:
            playlist_idx = playlist_idx % playlist_len
            draw(playlist_idx, playlist, playlist_len)
            new_selection = False


if len(sys.argv) == 1:
    sys.exit("Usage: pls [OPTIONS] URL [URL...] \n\nplaylist-select: error: You must provide at least one URL.")

sys.argv.pop(0)
PLAYLIST_URL = sys.argv.pop(0)

playlist_items = 50 

for arg in sys.argv:
    if "=" in arg:
        split_arg = arg.split("=")

        match split_arg[0]:
            case "--items" | "-i":
                playlist_items = split_arg[1]

PLAYLIST = get_playlist_data(PLAYLIST_URL, playlist_items)
PLAYLIST_LEN = len(PLAYLIST)
playlist_idx = 0

DEFAULT_MPV_COMMAND = ['mpv', '--ytdl-raw-options=cookies-from-browser=firefox']

select(PLAYLIST, playlist_idx, PLAYLIST_LEN, DEFAULT_MPV_COMMAND)

