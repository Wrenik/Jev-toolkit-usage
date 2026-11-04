<#
.SYNOPSIS
  Install all six Jev toolkit repositories into one virtual environment, in dependency order.

.DESCRIPTION
  No prompts. Steps: clone (or update) the six repositories, create one venv, pip-install them
  (usage first), create JEV_HOME and its .env, run `python -m jev_core check`.
  The TypeSafe key is read from the environment variable TYPESAFE_API_KEY if it is set; otherwise
  .env is created with an empty key and you fill it in later. The key is never printed.

.PARAMETER Dir
  Where the clones and the venv go (default: .\jev-toolkit-all).
.PARAMETER Source
  Base URL or folder the repositories are cloned from (default: https://github.com/Wrenik).
  Before the repositories are public, point it at a folder that holds local clones, e.g. C:\src\jev-repos.
.PARAMETER JevHome
  Data folder (default: $env:JEV_HOME, else ~\.jev-toolkit).
.PARAMETER Offline
  Run the final check with the fake judge (JEV_JUDGE=fake): no key and no network needed.
#>
[CmdletBinding()]
param(
    [string]$Dir = (Join-Path (Get-Location) "jev-toolkit-all"),
    [string]$Source = "https://github.com/Wrenik",
    [string]$JevHome = $(if ($env:JEV_HOME) { $env:JEV_HOME } else { Join-Path $HOME ".jev-toolkit" }),
    [switch]$Offline
)
$ErrorActionPreference = "Stop"

# Dependency order: usage is the base; Scanner is optional for FactCheck; Sources needs FactCheck.
$repos = "Jev-toolkit-usage", "Jev-toolkit-Scanner", "Jev-toolkit-Compiler",
         "Jev-toolkit-FactCheck", "Jev-toolkit-Monitor", "Jev-toolkit-Sources"

function Run([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "failed: $Exe $($Arguments -join ' ')" }
}

New-Item -ItemType Directory -Force -Path $Dir | Out-Null
$Dir = (Resolve-Path $Dir).Path

foreach ($r in $repos) {
    $target = Join-Path $Dir $r
    if (Test-Path (Join-Path $target ".git")) {
        Write-Host "update $r"
        Run git @("-C", $target, "pull", "--ff-only", "--quiet")
    } else {
        Write-Host "clone  $r"
        $url = if (Test-Path $Source) { Join-Path (Resolve-Path $Source).Path $r } else { "$($Source.TrimEnd('/'))/$r.git" }
        Run git @("clone", "--quiet", $url, $target)
    }
}

$venv = Join-Path $Dir ".venv"
if (-not (Test-Path $venv)) { Run python @("-m", "venv", $venv) }
$py = Join-Path $venv "Scripts\python.exe"
Run $py @("-m", "pip", "install", "--quiet", "--upgrade", "pip")

# The first install pulls the real dependencies (typesafe-sdk). The others use --no-deps because their
# git-URL dependencies on each other are already satisfied by the editable installs above them.
Run $py @("-m", "pip", "install", "--quiet", "-e", (Join-Path $Dir "Jev-toolkit-usage"))
foreach ($r in $repos | Select-Object -Skip 1) {
    Run $py @("-m", "pip", "install", "--quiet", "--no-deps", "-e", (Join-Path $Dir $r))
}

# JEV_HOME and its .env, without asking anything.
New-Item -ItemType Directory -Force -Path $JevHome | Out-Null
$envFile = Join-Path $JevHome ".env"
if (-not (Test-Path $envFile)) {
    $key = if ($env:TYPESAFE_API_KEY) { $env:TYPESAFE_API_KEY } else { "" }
    Set-Content -Path $envFile -Encoding ascii -Value @("TYPESAFE_API_KEY=$key", "JEV_MODEL=jev-1.14.0")
    Write-Host "created $envFile (key $(if ($key) { 'taken from the environment' } else { 'empty: fill it in later' }))"
} else {
    Write-Host "kept existing $envFile"
}

$env:JEV_HOME = $JevHome
if ($Offline) { $env:JEV_JUDGE = "fake" }
Write-Host "`nrunning: python -m jev_core check"
& $py -m jev_core check
$rc = $LASTEXITCODE
Write-Host "`nVenv: $venv   (activate: $venv\Scripts\Activate.ps1)"
Write-Host "Persist the data folder for new shells if it is not the default:  setx JEV_HOME `"$JevHome`""
if ($rc -ne 0) { Write-Host "check exited with $rc (no key yet? rerun with -Offline to test without one)" }
exit $rc
