# obswsgui

GUI for interacting with OBS through a WebSocket server.

## Downloads

Check the [GitHub releases](https://github.com/lusciousdev/obswsgui/releases).

## Using obswsgui

### Connecting to a WebSocket server

Input the IP address, port, and password for the OBS WebSocket server you wish to connect to.

<img src="./.github/images/connection_screen.png" width=450 align="center">

### Adding images

All image URLs must be accessible by the OBS client you are interfacing with. If you want to add an image that you have locally your best bet is uploading to a site like imgur and copying the URL.

### Manipulating sources

Click and drag to move, click corners or sides to resize. If a source is underneath something you can double click to cycle through the sources under your mouse.

### Duplicating sources

Duplicated sources will be created with the same position and size as the original.

### Moving sources to the top of the stack

To reorder images you can hit move to the front when selecting one of the moveable sources. This will move it to the front of the scene for you and the OBS server.

## Running from source

Just run ./src/main.py, you'll need to install PIL and simpleobsws