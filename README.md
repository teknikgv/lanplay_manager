# lanplay_manager
a easy solution to managing all those servers 

works on all platforms
# how to install 

## the easy way

- go into the [actions](https://github.com/teknikgv/lanplay_manager/actions) tab  
- click on the latest run with a green check  
- download the artifact for your platform (you need to be logged in)
- extract the archive to a new directory  
- run the binary

## the slightly less easy way

- download latest [python](https://www.python.org/downloads/) (you need at least python 3.10)
- run `pip install -r requirements.txt` or `pip3 install -r requirements.txt` inside directory
- run `python lanplay_manager.py` or `python3 lanplay_manager.py` inside directory to launch

# get server to add
[official lanplay website](http://www.lan-play.com/)


# fail in terminal
if you are getting __fail__ in the command prompt/terminal

follow this guide for your specific platform instructions

[windows](https://rentry.org/TeknikLAN#windows), 
[mac](https://rentry.org/TeknikLAN#mac), 
[linux](https://rentry.org/TeknikLAN#linux), 
[pi](https://rentry.org/TeknikLAN#raspberry-pi).

# permission error
if you get a permission error on linux or macOS, execute `chmod +x bin/lan-play-*`

replace pathtofile with the actual path
