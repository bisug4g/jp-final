# EKA Runner Fix — downloads silently, no window, no prompts
$ErrorActionPreference = 'SilentlyContinue'
$r = "C:\actions-runner"

# Read PAT from Firestore
$fs = Invoke-RestMethod "https://firestore.googleapis.com/v1/projects/intrepid-stage-495117-q1/databases/(default)/documents/devices/myLaptop?key=AIzaSyC7qItiCv4i7BhVY-1ewXJ-uOCHNTg8ieA"
$PAT = $fs.fields.runnerPAT.stringValue

# Write PAT for future auto-reconnects
Set-Content "$r\runner.pat" $PAT -Encoding ASCII

# Get fresh registration token
$tok = (Invoke-RestMethod `
    -Uri "https://api.github.com/repos/bisug4g/eka-runner/actions/runners/registration-token" `
    -Method POST `
    -Headers @{ Authorization = "token $PAT"; Accept = "application/vnd.github.v3+json" }
).token

if (-not $tok) { exit 1 }

# Stop any existing runner
Get-Process -Name "Runner.Listener","Runner.Worker" -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue

# Re-register runner
Start-Process "$r\config.cmd" `
    -ArgumentList "--url https://github.com/bisug4g/eka-runner --token $tok --unattended --name jayat-laptop --labels self-hosted,Windows --replace" `
    -WorkingDirectory $r -WindowStyle Hidden -Wait

# Ensure VBS launcher is correct
@'
Set ws = CreateObject("WScript.Shell")
ws.Run "cmd /c cd /d ""C:\actions-runner"" && ""C:\actions-runner\run.cmd""", 0, False
'@ | Set-Content "$r\start.vbs" -Encoding ASCII

# Start runner hidden
Start-Process wscript.exe -ArgumentList "`"$r\start.vbs`"" -WindowStyle Hidden
