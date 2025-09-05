48 c7 c1 f5 ff ff ff   # get STDOUT_HANDLE (which is -11) 
48 83 ec 20
e8 GetStdHandle
48 83 c4 20
48 83 ec 28
48 89 c1
48 8D 15 2D 00 00 00
41 b8 0f 00 00 00
4c 8d 4c 24 20
48 c7 44 24 20 00 00 00 00
e8 WriteConsoleA
48 83 c4 28
b8 2c 00 00 00
48 31 c9
e8 ExitProcess
31 c0
c3
"hello world!" 0d 0a 00