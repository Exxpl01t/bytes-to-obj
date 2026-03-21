55
48 89 e5
48 83 ec 60

# fill in args for CreateWindowExA
48 c7 44 24 58 00 00 00 00   # lParam     = NULL
48 c7 44 24 50 00 00 00 00   # hInstance  = NULL
48 c7 44 24 48 00 00 00 00   # hMenu      = NULL
48 c7 44 24 40 00 00 00 00   # hWndParent = NULL
c7 44 24 38 a4 01 00 00      # nHeight    = 0x1a4 = 420
c7 44 24 30 a4 01 00 00      # nWidth     = 0x1a4 = 420
c7 44 24 28 64 00 00 00      # y          = 0x64  = 100
c7 44 24 20 64 00 00 00      # x          = 0x64  = 100
41 b9 00 00 00 10            # dwStyle    = 0x10000000 = WS_VISIBLE
4c 8d 05 1e 00 00 00         # lpWindowName = "My window made with bytes!"
48 8d 15 32 00 00 00         # lpClassName  = "STATIC"
b9 00 00 00 00               # dwExStyle  = 0

# call CreateWindowExA
e8 CreateWindowExA

# sleep for 420 ms forever
b9 a4 01 00 00    # 0x1a4 = 420
e8 Sleep

eb f4     # jmp back

c3        # 

"My window made with bytes!" 00
"STATIC" 00