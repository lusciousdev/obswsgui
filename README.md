# obswsgui

GUI for interacting with OBS through a WebSocket server.

## Downloads

Check the [GitHub releases](https://github.com/lusciousdev/obswsgui/releases).

## Using obswsgui

### Connecting directly to a WebSocket server

Download the obswsgui zip in the releases and run the exe contained within.

Input the IP address, port, and password for the OBS WebSocket server you wish to connect to. The person you are connecting to must have forwarded the port used for their WebSocket server in order for you to connect.

<img src="./.github/images/connection_screen.png" width=450 align="center">

### Using a proxy server to connect to a WebSocket server

If you wish to hide your IP address from the people connecting to your OBS WebSocket server, use the proxiedserver and proxiedclient executables in the release. You can run your own proxy backend using [obswsgui/backend.py](obswsgui/backend.py).

### Adding images

All image URLs must be accessible by the OBS client you are interfacing with. If you want to add an image that you have locally your best bet is uploading to a site like imgur and copying the URL.

### Adding text

There's a dropdown in the add dialog, select the type of source you need. There are a few special types of text sources.

#### Countdowns

Countdown sources are a timer that decrements to whatever date/time you set in the dialog. Max countdown timer is 24 hours, the default is 1 hour. The end time must be given in the format "YYYY-MM-DD HH:mm:ss" (24 hour time).

#### Stopwatches

Stopwatch sources count up . They can be paused or reset in the side panel when selected. 

#### Timers

Timer sources count down from a starting duration. They can be paused or reset in the side panel when selected.

### Manipulating sources

Click and drag to move, click corners or sides to resize. The circle up top is for rotating a source. If a source is underneath something you can double click to cycle through the sources under your mouse.

### Duplicating sources

Duplicated sources will be created with the same position, name, and size as the original. BE CAREFUL WITH SOURCES SHARING NAMES. Any changes you make to one source changes all sources that share it's name.

### Moving sources to the top of the stack

To reorder images you can hit move to the front when selecting one of the moveable sources. This will move it to the front of the scene for you and the OBS server.

## Running from source

Just run [obswsgui/\_\_main\_\_.py](obswsgui/__main__.py)

You'll need to install PIL and simpleobsws