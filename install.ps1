# install.ps1 — Installe (ou met à jour) noblogs-backup-lite sous Windows, puis lance l'outil.
#   Utilisation (PowerShell) :
#     powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.ps1 -UseBasicParsing | iex"
#     # sauvegarde directe d'un blog :
#     powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://raw.githubusercontent.com/muarf/noblogs-backup-lite/main/install.ps1 -UseBasicParsing | iex" sauvegarder monblog
$ErrorActionPreference = "Stop"

function Get-WriteLine($Text, $Color = "White") {
    Write-Host "  $Text" -ForegroundColor $Color
}

$TAG_URL   = "https://codeload.github.com/muarf/noblogs-backup-lite/zip/refs/tags/v2.1.1"
$MAIN_URL  = "https://codeload.github.com/muarf/noblogs-backup-lite/zip/refs/heads/main"
$TARGET    = Join-Path $env:USERPROFILE "noblogs-backup-lite"

Get-WriteLine "Installation de noblogs-backup-lite..." "Cyan"
Get-WriteLine "Répertoire d'installation : $TARGET"

# --- 1. Python requis ---
$py = $null
foreach ($c in @("py", "python")) {
    try {
        $p = Get-Command $c -ErrorAction Stop
        if ($p) { $py = $p.Source; break }
    } catch { }
}
if (-not $py) {
    Get-WriteLine "Python 3 est requis. Installez-le depuis https://www.python.org/downloads/" "Red"
    Get-WriteLine "(cochez 'Add python.exe to PATH' lors de l'installation)." "Red"
    exit 1
}

# --- 2. Téléchargement de la source (curl d'abord, fallback Invoke-WebRequest) ---
function Get-Archive($Url) {
    $tmp = New-Object System.Collections.Generic.List[string]
    # curl est livré avec Windows 10+ / Serveur : essaye d'abord
    try {
        $curl = Get-Command curl.exe -ErrorAction Stop
        $tmpFile = Join-Path $env:TEMP ("noblogs-" + [guid]::NewGuid().ToString() + ".zip")
        & $curl.Source -fsSL $Url -o $tmpFile | Out-Null
        if ($LASTEXITCODE -eq 0) { return @($true, $tmpFile) }
    } catch { }
    $tmpFile = Join-Path $env:TEMP ("noblogs-" + [guid]::NewGuid().ToString() + ".zip")
    Invoke-WebRequest -Uri $Url -OutFile $tmpFile -UseBasicParsing
    return @($true, $tmpFile)
}

$zipFile = $null
foreach ($url in @($TAG_URL, $MAIN_URL)) {
    try {
        $res = Get-Archive $url
        $zipFile = $res[1]
        if ((Get-Item $zipFile).Length -gt 5000) { break }
        $zipFile = $null
    } catch { $zipFile = $null }
}
if (-not $zipFile) {
    Get-WriteLine "Téléchargement impossible : curl/wget absents ou pas de réseau." "Red"
    exit 1
}

# --- 3. Extraction dans un dossier temporaire ---
$tmpExtract = Join-Path $env:TEMP ("noblogs-src-" + [guid]::NewGuid().ToString())
Expand-Archive -Path $zipFile -DestinationPath $tmpExtract -Force
Remove-Item $zipFile -Force -ErrorAction SilentlyContinue

$src = Get-ChildItem $tmpExtract -Directory | Where-Object { $_.Name -like "noblogs-backup-lite-*" } | Select-Object -First 1
if (-not $src -or -not (Test-Path (Join-Path $src.FullName "noblogs.bat"))) {
    Get-WriteLine "L'archive téléchargée est invalide." "Red"
    Remove-Item $tmpExtract -Recurse -Force -ErrorAction SilentlyContinue
    exit 1
}

# --- 4. Copie non-destructive (préserve backups/ et .venv/ existants) ---
New-Item -ItemType Directory -Path $TARGET -Force | Out-Null
Copy-Item (Join-Path $src.FullName "*") $TARGET -Recurse -Force
Remove-Item $tmpExtract -Recurse -Force -ErrorAction SilentlyContinue

if (Test-Path (Join-Path $TARGET ".venv\Scripts\python.exe")) {
    Get-WriteLine "Mis à jour" "Green"
} else {
    Get-WriteLine "Installé" "Green"
}

# --- 5. Lancement (noblogs.bat gère le venv + deps + assistant) ---
if ($args.Count -gt 0) {
    & (Join-Path $TARGET "noblogs.bat") @args
} else {
    & (Join-Path $TARGET "noblogs.bat")
}
exit $LASTEXITCODE