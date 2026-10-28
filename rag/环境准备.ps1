$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$AppRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $AppRoot

function Find-CompatiblePython {
    $candidates = @(
        @{ Exe = "py.exe"; Prefix = @("-3") },
        @{ Exe = "python.exe"; Prefix = @() },
        @{ Exe = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"); Prefix = @() }
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.Exe -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }
        $arguments = @($candidate.Prefix) + @(
            "-c",
            "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
        )
        & $command.Source @arguments *> $null
        if ($LASTEXITCODE -eq 0) {
            return @{
                Exe = $command.Source
                Prefix = $candidate.Prefix
            }
        }
    }
    return $null
}

function Install-Python {
    $version = "3.12.10"
    $fileName = "python-$version-amd64.exe"
    $installer = Join-Path $env:TEMP $fileName
    $url = "https://www.python.org/ftp/python/$version/$fileName"

    Write-Host "Python 3.10+ was not found."
    Write-Host "Downloading the official Python $version installer..."
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $installer

    Write-Host "Installing Python for the current user..."
    $process = Start-Process -FilePath $installer -Wait -PassThru -ArgumentList @(
        "/quiet",
        "InstallAllUsers=0",
        "PrependPath=1",
        "Include_test=0"
    )
    if ($process.ExitCode -ne 0) {
        throw "Python installer exited with code $($process.ExitCode)."
    }
}

Write-Host "=== Checking Python ==="
$python = Find-CompatiblePython
if (-not $python) {
    Install-Python
    $python = Find-CompatiblePython
}
if (-not $python) {
    throw "Python installation did not become available in the current session."
}

Write-Host "Using Python: $($python.Exe)"
$venvPython = Join-Path $AppRoot ".venv\Scripts\python.exe"
$streamlitReady = $false
if (Test-Path -LiteralPath $venvPython) {
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $venvPython -c "import streamlit" 2>$null | Out-Null
    $streamlitReady = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $previousErrorAction
}

if (-not $streamlitReady) {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Host "=== Creating local virtual environment ==="
        $venvArgs = @($python.Prefix) + @("-m", "venv", ".venv")
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & $python.Exe @venvArgs
        $venvExitCode = $LASTEXITCODE
        $ErrorActionPreference = $previousErrorAction
        if ($venvExitCode -ne 0 -or -not (Test-Path -LiteralPath $venvPython)) {
            throw "Failed to create the local virtual environment."
        }
    }

    Write-Host "=== Installing Streamlit dependencies ==="
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $venvPython -m pip install --upgrade pip --disable-pip-version-check
    $pipUpgradeExitCode = $LASTEXITCODE
    $pipInstallExitCode = 0
    if ($pipUpgradeExitCode -eq 0) {
        & $venvPython -m pip install -r requirements.txt --disable-pip-version-check
        $pipInstallExitCode = $LASTEXITCODE
    }
    $ErrorActionPreference = $previousErrorAction
    if ($pipUpgradeExitCode -ne 0) {
        throw "Failed to upgrade pip."
    }
    if ($pipInstallExitCode -ne 0) {
        throw "Failed to install dependencies from requirements.txt."
    }

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $venvPython -c "import streamlit; print('Streamlit', streamlit.__version__)"
    $verifyExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction
    if ($verifyExitCode -ne 0) {
        throw "Streamlit verification failed."
    }
}

Write-Host "=== Environment ready ==="
