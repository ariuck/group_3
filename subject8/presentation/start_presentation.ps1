# Single entry point. Run Windows HTTP server directly against the WSL source.
$ErrorActionPreference = 'Stop'
$canonical='\\wsl.localhost\Ubuntu\home\user1\group_3\subject8\presentation'
if (!(Test-Path -LiteralPath (Join-Path $canonical 'index.html'))) { throw 'WSL Ubuntu presentation source is unavailable.' }
$runtime=Join-Path $canonical 'private\runtime'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
function Listener([int]$port) {
    Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
}
function HttpJson([string]$url) {
    try { Invoke-RestMethod -Uri $url -TimeoutSec 2 -ErrorAction Stop } catch { return $null }
}
$deckScript=Join-Path $canonical 'serve_deck.py'
$deckListener=Listener 8765
if ($deckListener) {
    $owner=Get-CimInstance Win32_Process -Filter "ProcessId=$($deckListener.OwningProcess)"
    if (!$owner.CommandLine -or !$owner.CommandLine.Contains($deckScript)) {
        throw 'Port 8765 is occupied by another source. Close that server before starting the canonical presentation.'
    }
} else {
    $env:PYTHONUTF8='1'
    $py=Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) { $python=$py.Source; $pythonArgs=@('-3',('"'+$deckScript+'"')) }
    else { $python=(Get-Command python.exe -ErrorAction Stop).Source; $pythonArgs=@(('"'+$deckScript+'"')) }
    Start-Process -FilePath $python -ArgumentList $pythonArgs -WindowStyle Hidden -WorkingDirectory $env:TEMP -RedirectStandardOutput (Join-Path $runtime 'deck.stdout.log') -RedirectStandardError (Join-Path $runtime 'deck.stderr.log') | Out-Null
    for($i=0;$i -lt 30 -and !(Listener 8765);$i++) { Start-Sleep -Milliseconds 300 }
    if (!(Listener 8765)) { throw "Deck server did not start. See $runtime\deck.stderr.log" }
}
$demo=HttpJson 'http://127.0.0.1:8010/api/info'
if (!$demo) {
    if (Listener 8010) { throw 'Port 8010 is occupied but the demo API is unavailable.' }
    Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d','Ubuntu','--cd','/home/user1/group_3/subject8','--exec','.venv/bin/python','-u','app/server.py') -WindowStyle Hidden -WorkingDirectory $env:TEMP -RedirectStandardOutput (Join-Path $runtime 'demo.stdout.log') -RedirectStandardError (Join-Path $runtime 'demo.stderr.log') | Out-Null
    for($i=0;$i -lt 40;$i++) {
        Start-Sleep -Milliseconds 500
        $demo=HttpJson 'http://127.0.0.1:8010/api/info'
        if ($demo) { break }
    }
}
$deckResponse=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8765/index.html' -TimeoutSec 5
Write-Output 'Source: /home/user1/group_3/subject8/presentation'
Write-Output "Deck: http://127.0.0.1:8765/index.html#1 (HTTP $($deckResponse.StatusCode))"
Write-Output 'Live GUI demo (Q&A): http://127.0.0.1:8765/index.html#a17'
if ($demo) { Write-Output "Demo model ready: $($demo.ready)" }
else { Write-Warning "The deck is running. Demo startup is pending; see $runtime\demo.stderr.log" }
