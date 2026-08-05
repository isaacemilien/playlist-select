#!/usr/bin/env python3
import json
import subprocess
import sys
import termios
import tty
import requests
import datetime
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename="pls.log", level=logging.INFO)

def download_video(url, title, cookies_from_browser):
    """Downloads given url to your downloads folder using yt-dlp

    Args:
        url: String URL to be downloaded.
        title: String name given to file once downloaded.
        cookies_from_browser: String argument to use cookies from given browser in yt-dlp.
    """

    print(f"Downloading '{title}' to ~/Downloads/...", end='\r')
    subprocess.Popen(['yt-dlp', '-o', f'~/Downloads/%(title)s.%(ext)s', url, cookies_from_browser],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "\t" + title

def populate_playlist_interface(raw_dump, url, title):
    """Returns uniform dictionary of playlist data based two mandatory keys

    Args:
        raw_dump: Dictionary representing unchanged playlist data fetched from yt-dlp
        url: String representing key containing the URL in playlist items
        url: String representing key containing the title in playlist items
    """

    playlist_interface = []

    if title not in raw_dump["entries"][0]:
        title = url

    for entry in raw_dump["entries"]:
        # print(i)
        playlist_interface.append({'url': entry[url], 'title': entry[title]})

    return playlist_interface

def get_playlist_data(url, items = None):
    """Fetches playlist data from given URL using yt-dlp

    Args:
        url: String URL to fetch playlist data from.
        items: Number representing upper limit of items to fetch from playlist.
    """

    ytdlp_command = ['yt-dlp', '-J', '--flat-playlist', url]

    if items is not None: 
        ytdlp_command.extend(['--playlist-items', '1-' + str(items)])

    result = subprocess.run(
        ytdlp_command,
        capture_output=True,
        text=True,
        check=True
    )

    raw_dump = json.loads(result.stdout)

    return populate_playlist_interface(raw_dump, 'url', 'title')

def get_key():
    """Awaits then returns termainl key presses"""

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
    """Main loop, new cycles are triggered by key press events as opposed to on a set interval

    Args:
        playlist: Dictionary representing current playlist.
        playlist_idx: The playlist index to prepend selection character to.
        playlist_len: Number representing length of playlist.
        default_mpv_command: String representing base mpv and default configurations used in all calls.
    """

    playlists = []
    playlists.append({
        "playlist_data": playlist, 
        "playlist_idx": playlist_idx,
        "playlist_len": len(playlist)})

    draw(playlist_idx, playlist, playlist_len)
    new_selection = False
    search_text = ""
    search_result_found = False
    search_result_seed = -1
    cookies_from_browser = ""

    for command in default_mpv_command:
        if "cookies-from-browser" in command:
            cookies_from_browser = "--" + command[command.find("=")+1:]
    
    while True: 
        key = get_key()

        match key:
            case 'q':
                logger.info(f"{{'ts': '{datetime.datetime.now(datetime.timezone.utc).isoformat()}', 'level': 'info', 'msg': 'run completed', 'service': 'playlist-select'}}")
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
                draw(playlist_idx, playlist, playlist_len, "    >")

                try: 
                    playlists[-1]["playlist_idx"] = playlist_idx

                    new_playlist_data = get_playlist_data(playlist[playlist_idx]["url"]) 
                    playlists.append({
                        "playlist_data": new_playlist_data,
                        "playlist_idx": playlist_idx,
                        "playlist_len": len(new_playlist_data)})

                    playlist = playlists[-1]["playlist_data"]
                    playlist_idx = 0
                    playlist_len = playlists[-1]["playlist_len"]
                    new_selection = True

                except KeyError:
                    print("\nKey error, mostly likely trying to index into a non-playlist element")
                    new_selection = False

            case 'h':
                if len(playlists) > 1:
                    playlists.pop()
                    playlist = playlists[-1]["playlist_data"]
                    playlist_idx = playlists[-1]["playlist_idx"]
                    playlist_len = playlists[-1]["playlist_len"]
                    new_selection = True
            case '\r':
                draw(playlist_idx, playlist, playlist_len, "    >")
                subprocess.run(default_mpv_command + [playlist[playlist_idx]["url"]])
                new_selection = True
            case 'v':
                draw(playlist_idx, playlist, playlist_len, "    >")
                subprocess.run(default_mpv_command + [playlist[playlist_idx]["url"], '-ytdl-format=299+bestaudio'])
                new_selection = True

            case ':':
                user_index = input(":")
                if user_index.isdigit():
                    playlist_idx = int(user_index) - 1

                    new_selection = True

                elif user_index == 'p':
                    print("\n\nExit with playlist url: ", playlist[playlist_idx]["url"])
                    logger.info(f"{{'ts': '{datetime.datetime.now(datetime.timezone.utc).isoformat()}', 'level': 'info', 'msg': 'run completed', 'service': 'playlist-select'}}")

                    sys.exit(0) 

                elif user_index == 'w':
                    print("\n\nExit with all playlist urls: ")
                    for i in range(PLAYLIST_LEN):
                        print(playlist[i]["url"])
                    logger.info(f"{{'ts': '{datetime.datetime.now(datetime.timezone.utc).isoformat()}', 'level': 'info', 'msg': 'run completed', 'service': 'playlist-select'}}")

                    sys.exit(0) 

                elif user_index == 'd':
                    playlist[playlist_idx]["title"] = download_video(playlist[playlist_idx]["url"], playlist[playlist_idx]["title"], cookies_from_browser)
                    new_selection = True

                else:
                    print("Invalid command")
                    
                    continue

            case '/' | 'n' | 'N':
                if key == '/':
                    search_text = input("/")

                    search_result_found = False
                    search_result_seed = -1

                    for i in range(playlist_len):
                        if search_text.lower() in playlist[i]["title"].lower():
                            search_result_found = True
                            search_result_seed = i

                if search_result_found:
                    idx = playlist_idx
                    while not new_selection:
                        idx = idx - 1 if key == 'N' else idx + 1
                        idx = idx % playlist_len

                        if search_text.lower() in playlist[idx]["title"].lower():
                            playlist_idx = idx

                            new_selection = True
                        
            case _:
                print(f"No key binding found for key '{key}'.")

                continue


        if new_selection:
            playlist_idx = playlist_idx % playlist_len
            draw(playlist_idx, playlist, playlist_len)
            new_selection = False



logger.info(f"{{'ts': '{datetime.datetime.now(datetime.timezone.utc).isoformat()}', 'level': 'info', 'msg': 'run started', 'service': 'playlist-select'}}")

if len(sys.argv) == 1:
    sys.exit("Usage: pls [OPTIONS] URL [URL...] \n\nplaylist-select: error: You must provide at least one URL.")

sys.argv.pop(0)
playlist_url = sys.argv.pop(0)

playlist_items = 50 

search = ""

default_mpv_command = ['mpv']

for arg in sys.argv:
    if "=" in arg:
        split_arg = arg.split("=", 1)

        match split_arg[0]:
            case "--items" | "-i":
                playlist_items = split_arg[1]
            case "--mpv-raw-options" | "-r":
                default_mpv_command.append("--" + split_arg[1])
                
    if arg == "-yt" or arg == "-sc":
        search = arg

if len(search) > 1:
    playlist_url = f'{arg[1:]}search{playlist_items}:{playlist_url}'

PLAYLIST = get_playlist_data(playlist_url, playlist_items)
PLAYLIST_LEN = len(PLAYLIST)
playlist_idx = 0

select(PLAYLIST, playlist_idx, PLAYLIST_LEN, default_mpv_command)

