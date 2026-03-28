Param(
  [string]$Python = 'python'
)

if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
  Write-Error "Python executable '$Python' not found. Install Python 3.10+ and retry."
  exit 1
}

$Venv = ".venv"
if (-not (Test-Path $Venv)) {
  & $Python -m venv $Venv
  Write-Host "Created virtual environment: $Venv"
}

& "$Venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
if (Test-Path "requirements_api.txt") {
  python -m pip install -r requirements_api.txt
}
python -m pip install pytest pytest-cov

Write-Host "Setup complete. Activate the venv with: & $Venv\Scripts\Activate.ps1"