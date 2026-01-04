#!/usr/bin/env python3
import json
import subprocess
import sys
import termios
import tty
import requests

def populate_playlist_interface(raw_dump, url, title):

    playlist_interface = []

    for entry in raw_dump["entries"]:
        playlist_interface.append({'url': entry[url], 'title': entry[title]})

    return playlist_interface

def get_playlist_data(url, items, get_playlist_api = None):
    if get_playlist_api:
        payload = {'url': url, 'items': str(items)}

        r = requests.post(get_playlist_api, json=payload)

        raw_dump = json.loads(r.text)

        return populate_playlist_interface(raw_dump, 'url', 'title')

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
    print('\033[2J\033[H', end='')

    low = playlist_idx - (playlist_idx % 10) 
    high = playlist_len if low + 10 > playlist_len else low + 10

    for i in range(low, high):
        pref = selection_char if i == playlist_idx else " "
        print(pref, str(i + 1) + ".",playlist[i]["title"] )

def select(playlist, playlist_idx, playlist_len, default_mpv_command):
    draw(playlist_idx, playlist, playlist_len)
    
    while True: 
        key = get_key()

        match key:
            case 'q':
                sys.exit(0) 
            case 'j' | '\033[B':
                playlist_idx += 1
                new_selection = True
            case 'k' | '\033[A':
                playlist_idx -= 1
                new_selection = True
            case 'J' | '\033[B':
                playlist_idx += 10
                new_selection = True
            case 'K' | '\033[A':
                playlist_idx -= 10
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
            draw(playlist_idx, playlist, playlist_len)
            new_selection = False

PLAYLIST_URL = sys.argv[1]
PLAYLIST_ITEMS = sys.argv[2] if len(sys.argv) > 2 else 50
GET_PLAYLIST_API = sys.argv[3] if len (sys.argv) > 3 else None

PLAYLIST = get_playlist_data(PLAYLIST_URL, PLAYLIST_ITEMS, GET_PLAYLIST_API)
PLAYLIST_LEN = len(PLAYLIST)
playlist_idx = 0

DEFAULT_MPV_COMMAND = ['mpv', '--ytdl-raw-options=cookies-from-browser=firefox']

select(PLAYLIST, playlist_idx, PLAYLIST_LEN, DEFAULT_MPV_COMMAND)

