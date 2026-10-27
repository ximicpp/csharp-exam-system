$quizRoot = Split-Path -Parent $PSScriptRoot
$quizPython = Join-Path $quizRoot '.venv/Scripts'
if (!(Test-Path -LiteralPath (Join-Path $quizPython 'python.exe'))) { throw 'Create .venv and install dependencies; see README.md.' }
$env:VIRTUAL_ENV = Join-Path $quizRoot '.venv'
$env:PATH = $quizPython + ';' + $env:PATH
