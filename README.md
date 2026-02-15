# playlist-select
Linux command line tool for pulling a playlist using yt-dlp, and passing a selected item to MPV.

![Demo](https://github.com/user-attachments/assets/25bcc297-5339-45b5-b0e3-813a755612ad)

# Installation
With both yt-dlp and mpv installed either:
- Define as a nix input, for example: 

`playlist-select.url = "github:isaacemilien/playlist-select";` in your `flake.nix`. 
- Or simply clone and directly use with python.

# Usage
- `j` or `k` to move up and down by single entries.
- `h` or `l` to go up and down a level of nesting in a playlist.
- `enter` to play a playlist entry in MPV.
- `q` to exit.

You can also use:
- `J` or `K` to move up and down in increments of 10.
- `v` to play entry in lower resolution format if available.
- `p` to print the current elements url and exit.

# Examples
List first 50 results from playlist:

    pls https://www.youtube.com/@ethoslab/videos

Limiting results to specific amount:

    pls https://www.youtube.com/@ethoslab/videos --items=120
    
Passing raw MPV and yt-dlp commands:

    pls https://www.youtube.com/@ethoslab/videos --items=12 -r=--ytdl-raw-options=cookies-from-browser=firefox
    

