# SSMI Python
This code reads from (currently) Spotify to get the current song information to then be used to update a SteelSeries 
keyboard's OLED display.

# MacOS
Code is in, tutorial will be put in later. Make sure you have `python-daemon`, `requests`, and `spotipy` installed as root. To launch as daemon, just use `sudo python3 unix.py`.

# Windows
This is not for the lighthearted.

First, you will need Python 3.8 installed with `pywin32`, `requests`, and `spotipy` installed as root. You then need to set
some **system** `PATH` variables:
- `[PythonPath]\Python38-32\Scripts\`
- `[PythonPath]\Python38-32\`
- `[PythonPath]\Python38-32\Lib\site-packages`
- `[PythonPath]\Python38-32\Lib\site-packages\pywin32_system32`

Example:
`C:\Users\jackh\AppData\Local\Programs\Python\Python38-32\Lib\site-packages\pywin32_system32`

Change these as needed to sut your computer's structure.
**Restart your computer to ensure these variables are recognized.**

Next, you need to run the post install script at `[PythonPath]\Python38-32\Scripts\pywin32_postinstall.py`.

Next, you need to copy `[PythonPath]\Python38-32\Lib\site-packages\pywin32_system32\pywintypes38.dll` to 
`[PythonPath]\Python38-32\Lib\site-packages\win32`.

Next, you need to install the service. To do this, navigate to `service.py` in the Command Prompt 
and run `python service.py install`. **I have not tested what happens if the file is moved after installation, 
so undefined behavior may occur.** If you want to move the file after installation, run `pythin service.py remove`,
restart, move the file, then run the install command again and follow the directions from here.

You're almost done! Run `services.msc`, then navigate to the `SteelSeries Media Integration Service`. Don't start it yet!
Double click on the service and navigate to the `Log On` tab. Select `This Account`, 
then browse for your username (enter it into the box then click `Check Names` then `OK`). After that, enter your password
twice and click `Apply` and then `OK`. You will be granted the permission to start services.

So close! Run the service. However, it won't work. This was just to generate the config file. This will be under your
user directory under a folder called `SSMI`. Open `creds.json` and enter your information. Save it and close it.

Finally, go back to the Services window and double click on the service again, now set the startup type to `Automatic`
and click `Apply` then `OK`.

**Congratulations! Close your windows, restart your computer and you are done!**
