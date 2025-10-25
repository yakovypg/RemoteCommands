Set wshNetwork = CreateObject("WScript.Network")
username = wshNetwork.UserName

Set WshShell = CreateObject("WScript.Shell")
path = "C:\Users\" & username & "\Documents\Executor\run-executor.bat"
WshShell.Run Chr(34) & path & Chr(34), 0, False

Set WshShell = Nothing
Set wshNetwork = Nothing
