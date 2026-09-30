Option Explicit
Dim shell, files, folder, pythonw, app
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
pythonw = "C:\Users\Sakam\AppData\Local\Programs\Python\Python313\pythonw.exe"
app = folder & "\Co Caro.pyw"
shell.Run """" & pythonw & """ """ & app & """", 1, False
