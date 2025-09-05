@echo off
python bytes-to-obj.py main.as

:: set /console option for console exe, /exe option for GUI exe
golink /entry start /fo obj.exe obj.obj Kernel32.dll User32.dll /exe


obj.exe