#!/usr/bin/env python3
import json
import subprocess
import sys

def get_playlist_data(url):
    result = subprocess.run(
        ['yt-dlp', '-J', '--flat-playlist', url],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(result.stdout)

playlist_url = sys.argv[1]

data = get_playlist_data(playlist_url)
print(data)

