# Windows PowerShell 5.1+ / PowerShell 7. No administrator rights required.
[CmdletBinding()]
param(
    [string]$ExistingSdkRoot,
    [switch]$OpenCode
)

$ErrorActionPreference = 'Stop'
$examRoot = $PSScriptRoot
$examTools = Join-Path $examRoot '.tools'
$examSdkRoot = Join-Path $examTools 'dotnet11'
$examDotnet = Join-Path $examSdkRoot 'dotnet.exe'
$examVersion = (Get-Content -LiteralPath (Join-Path $examRoot 'global.json') -Raw | ConvertFrom-Json).sdk.version

function Invoke-ExamCommand {
    param([string]$Executable, [string[]]$Arguments, [string]$Step)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Step failed with exit $LASTEXITCODE." }
}

function Find-ExamCode {
    $command = Get-Command code -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) { return $command.Source }
    foreach ($base in @($env:LOCALAPPDATA, $env:ProgramFiles)) {
        if (!$base) { continue }
        $relative = if ($base -eq $env:LOCALAPPDATA) { 'Programs/Microsoft VS Code/bin/code.cmd' } else { 'Microsoft VS Code/bin/code.cmd' }
        $candidate = Join-Path $base $relative
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

function Test-ExamSdk {
    param([string]$SdkRoot)
    $executable = Join-Path $SdkRoot 'dotnet.exe'
    if (!(Test-Path -LiteralPath $executable) -or !(Test-Path -LiteralPath (Join-Path $SdkRoot "sdk/$examVersion"))) { return $false }
    $versionOutput = & $executable --version 2>&1
    return $LASTEXITCODE -eq 0 -and ($versionOutput | Out-String).Trim() -eq $examVersion
}

Push-Location -LiteralPath $examRoot
try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw 'Use bash setup.sh on Linux/macOS.' }
    if ($examVersion -notmatch '^11\.\d+\.\d+(?:-[A-Za-z0-9.]+)?$') { throw 'Expected a pinned .NET 11 SDK in global.json.' }
    foreach ($required in @('CSharpExam.slnx', '.vscode/extensions.json')) {
        if (!(Test-Path -LiteralPath (Join-Path $examRoot $required))) { throw "Missing package file: $required" }
    }
    New-Item -ItemType Directory -Path $examTools -Force | Out-Null
    $env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    $env:DOTNET_NOLOGO = '1'
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()

    Write-Host "[1/4] Prepare .NET SDK $examVersion"
    if (!(Test-ExamSdk $examSdkRoot)) {
        if (Test-Path -LiteralPath (Join-Path $examSdkRoot "sdk/$examVersion")) {
            throw 'The requested SDK exists but cannot run. Diagnose its output; do not overwrite it.'
        }
        if ($ExistingSdkRoot) {
            $sourceRoot = (Resolve-Path -LiteralPath $ExistingSdkRoot).Path
            if (!(Test-ExamSdk $sourceRoot)) { throw 'The supplied SDK root does not provide the requested version.' }
            if (Test-Path -LiteralPath $examSdkRoot) { throw 'Existing destination must be preserved; no junction was created.' }
            New-Item -ItemType Junction -Path $examSdkRoot -Target $sourceRoot | Out-Null
        } else {
            $installer = Join-Path $examTools 'dotnet-install.ps1'
            Invoke-WebRequest -UseBasicParsing -Uri 'https://dot.net/v1/dotnet-install.ps1' -OutFile $installer
            $shell = (Get-Process -Id $PID).Path
            & $shell -NoProfile -ExecutionPolicy Bypass -File $installer -Version $examVersion -InstallDir $examSdkRoot -Architecture $architecture -NoPath
            if ($LASTEXITCODE -ne 0) { throw "SDK installation failed with exit $LASTEXITCODE." }
        }
    }
    if (!(Test-ExamSdk $examSdkRoot)) { throw 'Installed SDK cannot resolve the pinned version.' }
    $runtimes = & $examDotnet --list-runtimes
    if ($LASTEXITCODE -ne 0 -or !($runtimes -match '^Microsoft\.NETCore\.App 11\.0\.')) {
        throw 'The local .NET 11 runtime is missing.'
    }
    $env:DOTNET_ROOT = $examSdkRoot
    Set-Item -LiteralPath "Env:DOTNET_ROOT_$($architecture.ToUpperInvariant())" -Value $examSdkRoot
    $env:PATH = (@($examSdkRoot) + @($env:PATH -split ';' | Where-Object { $_ -and $_ -ne $examSdkRoot })) -join ';'
    & $examDotnet --version
    if ($LASTEXITCODE -ne 0) { throw 'SDK resolution failed.' }

    Write-Host '[2/4] Prepare VS Code and recommended extensions'
    $examCode = Find-ExamCode
    if (!$examCode) {
        $codePlatform = switch ($architecture) {
            'x64' { 'win32-x64-user' }
            'arm64' { 'win32-arm64-user' }
            default { throw "Unsupported VS Code architecture: $architecture" }
        }
        $codeInstaller = Join-Path $examTools 'VSCodeUserSetup.exe'
        Invoke-WebRequest -UseBasicParsing -Uri "https://update.code.visualstudio.com/latest/$codePlatform/stable" -OutFile $codeInstaller
        $installedCode = Start-Process -FilePath $codeInstaller -ArgumentList @('/VERYSILENT', '/NORESTART', '/MERGETASKS=!runcode') -WindowStyle Hidden -Wait -PassThru
        if ($installedCode.ExitCode -ne 0) { throw "VS Code installation failed with exit $($installedCode.ExitCode)." }
        $examCode = Find-ExamCode
        if (!$examCode) { throw 'VS Code installer completed but code.cmd was not found.' }
    }
    Invoke-ExamCommand -Executable $examCode -Arguments @('--version') -Step 'VS Code version check'
    $extensions = (Get-Content -LiteralPath (Join-Path $examRoot '.vscode/extensions.json') -Raw | ConvertFrom-Json).recommendations
    if (!$extensions) { throw 'No VS Code extension recommendations were found.' }
    $installedExtensions = @(& $examCode --list-extensions)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot list VS Code extensions.' }
    foreach ($extension in $extensions) {
        if ($extension -notmatch '^[A-Za-z0-9-]+\.[A-Za-z0-9-]+$') { throw "Invalid extension ID: $extension" }
        if ($installedExtensions -contains $extension) {
            Write-Host "Already installed: $extension"
        } else {
            Invoke-ExamCommand -Executable $examCode -Arguments @('--install-extension', $extension) -Step "Install $extension"
        }
    }
    $installedExtensions = @(& $examCode --list-extensions)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot verify VS Code extensions.' }
    foreach ($extension in $extensions) {
        if ($installedExtensions -notcontains $extension) { throw "Extension installation was not verified: $extension" }
    }

    Write-Host '[3/4] Restore solution dependencies'
    Invoke-ExamCommand -Executable $examDotnet -Arguments @('restore', 'CSharpExam.slnx', '--nologo', '--verbosity', 'quiet', '-m:4') -Step 'Solution restore'

    Write-Host '[4/4] Compile and run an independent environment check'
    $checkRoot = Join-Path $examTools 'environment-check'
    New-Item -ItemType Directory -Path $checkRoot -Force | Out-Null
    $checkProject = Join-Path $checkRoot 'EnvironmentCheck.csproj'
    $checkSource = Join-Path $checkRoot 'Program.cs'
    $utf8 = [Text.UTF8Encoding]::new($false)
    [IO.File]::WriteAllText($checkProject, @'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net11.0</TargetFramework>
    <LangVersion>14.0</LangVersion>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
'@, $utf8)
    [IO.File]::WriteAllText($checkSource, @'
if (Environment.Version.Major != 11)
{
    Console.Error.WriteLine($"Expected .NET 11, got {Environment.Version}.");
    return 1;
}
Console.WriteLine($"PASS: environment smoke (.NET {Environment.Version})");
return 0;
'@, $utf8)
    Invoke-ExamCommand -Executable $examDotnet -Arguments @('run', '--project', $checkProject, '-c', 'Release', '--no-launch-profile', '--verbosity', 'quiet') -Step 'Environment check'
    if ($OpenCode) {
        Invoke-ExamCommand -Executable $examCode -Arguments @('--new-window', $examRoot) -Step 'Open VS Code'
    }
    Write-Host 'PASS: environment ready'
    Write-Host 'Reload an existing VS Code window and create a new terminal; Ctrl+Shift+B builds and F5 debugs the current question.'
    Write-Host 'Compile-error questions remain unchanged; setup does not build or grade question answers.'
} finally {
    Pop-Location
}
