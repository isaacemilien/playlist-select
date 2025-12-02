#!/usr/bin/env python3
import json
import subprocess
import sys
import termios
import tty

def get_playlist_data(url, items):
    result = subprocess.run(
        ['yt-dlp', '-J', '--flat-playlist', '--playlist-items', '1-' + str(items), url],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(result.stdout)

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

def draw(playlist_idx, playlist, playlist_len):
    print('\033[2J\033[H', end='')

    low = playlist_idx - (playlist_idx % 10) 
    high = playlist_len if low + 10 > playlist_len else low + 10

    for i in range(low, high):
        pref = ">" if i == playlist_idx else " "
        print(pref, str(i + 1) + ".",playlist[i]["title"] )

def select(playlist, playlist_idx, playlist_len):
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
            case '\r':
                subprocess.run(['mpv', playlist[playlist_idx]["url"]])
                new_selection = True
            case 'v':
                subprocess.run(['mpv', playlist[playlist_idx]["url"], '-ytdl-format=299+bestaudio'])
                new_selection = True

        if new_selection:
            draw(playlist_idx, playlist, playlist_len)
            new_selection = False


playlist_url = sys.argv[1]
playlist_items = sys.argv[2] if len(sys.argv) > 2 else 50

playlist = get_playlist_data(playlist_url, playlist_items)["entries"]
playlist_len = len(playlist)
playlist_idx = 0

select(playlist, playlist_idx, playlist_len)

