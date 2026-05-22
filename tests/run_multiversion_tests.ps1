<#
.SYNOPSIS
    Install aepp from source and run import tests against Python 3.12, 3.13, and 3.14
    in fully isolated virtual environments.

.DESCRIPTION
    For each target Python version the script:
      1. Locates the interpreter via the Windows Python Launcher (py.exe).
      2. Creates a fresh temporary virtual environment.
      3. Installs aepp from the local source tree (pip install -e .[dev] or plain install).
      4. Runs tests/test_import_modules.py with pytest.
      5. Reports a per-version pass/fail summary.

    Temporary environments are created under $env:TEMP\aepp_test_envs and are
    deleted at the end unless -KeepEnvs is specified.

.PARAMETER KeepEnvs
    Keep the virtual environments after the run (useful for debugging).

.PARAMETER PythonVersions
    Override the default list of Python versions to test.
    Example: -PythonVersions @("3.12","3.13")

.EXAMPLE
    .\tests\run_multiversion_tests.ps1
    .\tests\run_multiversion_tests.ps1 -KeepEnvs
    .\tests\run_multiversion_tests.ps1 -PythonVersions @("3.12","3.13")
#>

[CmdletBinding()]
param(
    [switch]$KeepEnvs,
    [string[]]$PythonVersions = @("3.12", "3.13", "3.14")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── helpers ────────────────────────────────────────────────────────────────────

function Write-Header([string]$text) {
    $line = "=" * 70
    Write-Host ""
    Write-Host $line                -ForegroundColor Cyan
    Write-Host "  $text"           -ForegroundColor Cyan
    Write-Host $line                -ForegroundColor Cyan
}

function Write-Step([string]$text) {
    Write-Host "  >> $text" -ForegroundColor Yellow
}

function Write-OK([string]$text) {
    Write-Host "  [PASS] $text" -ForegroundColor Green
}

function Write-Fail([string]$text) {
    Write-Host "  [FAIL] $text" -ForegroundColor Red
}

# ── resolve repo root (parent of the script's directory) ──────────────────────

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Split-Path -Parent $ScriptDir
$TestFile  = Join-Path $ScriptDir "test_import_modules.py"

if (-not (Test-Path $RepoRoot\pyproject.toml)) {
    Write-Error "Cannot locate pyproject.toml. Expected repo root: $RepoRoot"
    exit 1
}

if (-not (Test-Path $TestFile)) {
    Write-Error "Cannot find test file: $TestFile"
    exit 1
}

# ── check for Python Launcher ─────────────────────────────────────────────────

$PyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
if ($null -eq $PyLauncher) {
    Write-Error (
        "The Windows Python Launcher (py.exe) was not found.`n" +
        "Install it from https://www.python.org/downloads/ and make sure " +
        "'Add Python to PATH' and 'py launcher' options are enabled."
    )
    exit 1
}

# ── create a parent directory for all temp envs ───────────────────────────────

$EnvRoot = Join-Path $env:TEMP "aepp_test_envs"
if (-not (Test-Path $EnvRoot)) {
    New-Item -ItemType Directory -Path $EnvRoot | Out-Null
}

# ── results table ─────────────────────────────────────────────────────────────

$Results = [ordered]@{}

# ── main loop ─────────────────────────────────────────────────────────────────

foreach ($Version in $PythonVersions) {

    Write-Header "Python $Version"
    $Results[$Version] = "SKIP"

    # 1. Verify interpreter availability
    Write-Step "Checking for Python $Version via py launcher ..."
    $PythonExe = $null
    try {
        $VerOutput = & py "-$Version" --version 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Exit code $LASTEXITCODE" }
        $PythonExe = "py"
        Write-OK "Found: $VerOutput"
    } catch {
        Write-Fail "Python $Version not found (py -$Version failed). Skipping."
        $Results[$Version] = "SKIP (interpreter not found)"
        continue
    }

    # 2. Create isolated virtual environment
    $EnvPath = Join-Path $EnvRoot "venv_$($Version.Replace('.','_'))"
    if (Test-Path $EnvPath) {
        Write-Step "Removing stale environment: $EnvPath"
        Remove-Item -Recurse -Force $EnvPath
    }
    Write-Step "Creating virtual environment at $EnvPath ..."
    & py "-$Version" -m venv $EnvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to create venv for Python $Version"
        $Results[$Version] = "FAIL (venv creation)"
        continue
    }
    Write-OK "Virtual environment created."

    $VenvPython = Join-Path $EnvPath "Scripts\python.exe"
    $VenvPip    = Join-Path $EnvPath "Scripts\pip.exe"

    # 3. Upgrade pip silently
    Write-Step "Upgrading pip ..."
    & $VenvPython -m pip install --upgrade pip --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "pip upgrade failed for Python $Version"
        $Results[$Version] = "FAIL (pip upgrade)"
        continue
    }

    # 4. Install aepp from source
    Write-Step "Installing aepp from source ($RepoRoot) ..."
    & $VenvPip install "$RepoRoot" --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "aepp installation failed for Python $Version"
        $Results[$Version] = "FAIL (install)"
        continue
    }
    Write-OK "aepp installed."

    # 5. Install pytest inside the venv
    Write-Step "Installing pytest ..."
    & $VenvPip install pytest --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "pytest installation failed for Python $Version"
        $Results[$Version] = "FAIL (pytest install)"
        continue
    }

    # 6. Run the import tests
    Write-Step "Running import tests ..."
    & $VenvPython -m pytest $TestFile -v --tb=short 2>&1 | Tee-Object -Variable TestOutput
    $ExitCode = $LASTEXITCODE

    if ($ExitCode -eq 0) {
        Write-OK "All import tests passed for Python $Version."
        $Results[$Version] = "PASS"
    } else {
        Write-Fail "One or more import tests FAILED for Python $Version (exit code $ExitCode)."
        $Results[$Version] = "FAIL (tests)"
    }

    # 7. Clean up unless -KeepEnvs
    if (-not $KeepEnvs) {
        Write-Step "Cleaning up $EnvPath ..."
        Remove-Item -Recurse -Force $EnvPath
    }
}

# ── summary ───────────────────────────────────────────────────────────────────

Write-Header "Summary"
$AllPassed = $true
foreach ($Ver in $Results.Keys) {
    $Status = $Results[$Ver]
    if ($Status -eq "PASS") {
        Write-OK "Python $Ver : $Status"
    } elseif ($Status -like "SKIP*") {
        Write-Host "  [SKIP] Python $Ver : $Status" -ForegroundColor DarkYellow
    } else {
        Write-Fail "Python $Ver : $Status"
        $AllPassed = $false
    }
}
Write-Host ""

if ($AllPassed) {
    Write-Host "All tested versions passed." -ForegroundColor Green
    exit 0
} else {
    Write-Host "One or more versions failed. See output above." -ForegroundColor Red
    exit 1
}
