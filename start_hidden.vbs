Set FSO = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
currentDir = FSO.GetParentFolderName(WScript.ScriptFullName)

' 1. Start Backend Server silently (0 = hide window, False = async)
WshShell.Run "cmd /c """ & currentDir & "\run_backend.bat""", 0, False

' 2. Wait 3 seconds for backend initialization
WScript.Sleep 3000

' 3. Start Ngrok Tunnel silently
WshShell.Run "cmd /c """ & currentDir & "\run_ngrok.bat""", 0, False

