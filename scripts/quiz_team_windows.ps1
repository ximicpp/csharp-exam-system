param(
    [ValidateSet('Prepare', 'Start', 'Stop', 'Status', 'Autostart', 'RemoveAutostart', 'InstallTask', 'RemoveTask', 'TaskDefinition', 'Run', 'Firewall', 'Trust', 'DefaultAdmin')]
    [string]$Action = 'Status',
    [string]$Address,
    [ValidateSet('Http', 'Https')][string]$Protocol = 'Http',
    [Alias('HttpsPort')][ValidateRange(1024, 65535)][int]$WebPort = 8080,
    [ValidateRange(1024, 65535)][int]$BackendPort = 8769,
    [string]$DataDirectory = (Join-Path $env:USERPROFILE 'CSharpQuizPublic-data')
)
$ErrorActionPreference = 'Stop'
$repoDirectory = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'env.ps1')
$DataDirectory = [IO.Path]::GetFullPath($DataDirectory)
$configPath = Join-Path $DataDirectory 'deployment.json'
$hostScript = Join-Path $PSScriptRoot 'quiz_team_host.py'
$startupPath = Join-Path ([Environment]::GetFolderPath('Startup')) 'CSharpQuizPublic.lnk'
if ($Protocol -eq 'Https' -and -not $PSBoundParameters.ContainsKey('WebPort')) { $WebPort = 8443 }

function Read-Deployment {
    if (-not (Test-Path -LiteralPath $configPath)) {
        throw "Deployment config not found: $configPath. Run Prepare first or pass the existing -DataDirectory."
    }
    $deployment = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($deployment.data_directory -ne $DataDirectory -or $deployment.repository -ne $repoDirectory) {
        throw 'Deployment belongs to another directory or checkout. Preserve it and use its original checkout.'
    }
    # Older HTTPS configurations remain usable for Stop / Start before re-preparing.
    if (-not $deployment.PSObject.Properties['web_port']) {
        $deployment | Add-Member -NotePropertyName web_port -NotePropertyValue $deployment.https_port
        $deployment | Add-Member -NotePropertyName protocol -NotePropertyValue 'https'
    }
    return $deployment
}

function Get-QuizHost {
    $pidPath = Join-Path $DataDirectory 'host.pid'
    if (-not (Test-Path -LiteralPath $pidPath)) { return $null }
    $hostPidValue = [int](Get-Content -LiteralPath $pidPath -Raw)
    $hostProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $hostPidValue"
    if ($hostProcess -and $hostProcess.CommandLine -and $hostProcess.CommandLine.Contains($hostScript) -and $hostProcess.CommandLine.Contains($configPath)) {
        return $hostProcess
    }
    # S4U process command lines are hidden from the interactive token. Verify creation time,
    # image name and the protected deployment record; a reused PID must never match.
    $statePath = Join-Path $DataDirectory 'host-state.json'
    if ($hostProcess -and -not $hostProcess.CommandLine -and $hostProcess.CreationDate -and (Test-Path -LiteralPath $statePath)) {
        $recordedDeployment = Read-Deployment
        if ($hostProcess.Name -ne [IO.Path]::GetFileName($recordedDeployment.python)) { return $null }
        $hostState = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($hostState.pid -eq $hostPidValue -and $hostState.data_directory -eq $DataDirectory -and
                [Math]::Abs([long]$hostState.created_filetime - $hostProcess.CreationDate.ToFileTimeUtc()) -lt 10) {
            return $hostProcess
        }
    }
    return $null
}

if ($Action -eq 'Prepare') {
    if (-not (Test-Path -LiteralPath (Join-Path $repoDirectory 'data/quiz-team-roster.json'))) { throw 'Create data/quiz-team-roster.json from the example before Prepare.' }
    $parsedAddress = $null
    if (-not [Net.IPAddress]::TryParse($Address, [ref]$parsedAddress) -or
        $parsedAddress.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork -or
        [Net.IPAddress]::IsLoopback($parsedAddress) -or $Address -eq '0.0.0.0') {
        throw 'Supply this machine''s LAN IPv4 address with -Address.'
    }
    if (-not (Get-NetIPAddress -AddressFamily IPv4 -IPAddress $Address -ErrorAction SilentlyContinue)) {
        throw 'Address must belong to this machine.'
    }
    if ($WebPort -eq $BackendPort) { throw 'Web and backend ports must differ.' }
    if (Test-Path -LiteralPath $configPath) { $null = Read-Deployment }
    elseif ((Test-Path -LiteralPath $DataDirectory) -and (Get-ChildItem -LiteralPath $DataDirectory -Force)) {
        throw 'Data directory is not empty and has no deployment config; choose a new directory. No files or permissions changed.'
    }
    if (Get-QuizHost) { throw 'Stop the existing deployment before preparing configuration.' }
    New-Item -ItemType Directory -Path $DataDirectory -Force | Out-Null
    # Data, initial password and CA private keys inherit an owner-only ACL.
    $ownerSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $existingAcl = Get-Acl -LiteralPath $DataDirectory
    if ($existingAcl.GetOwner([Security.Principal.SecurityIdentifier]) -ne $ownerSid) {
        throw 'Data directory must be owned by the current deployment user; no ownership was changed.'
    }
    $directoryAcl = [Security.AccessControl.DirectorySecurity]::new()
    $directoryAcl.SetSecurityDescriptorSddlForm(
        ('D:P(A;OICI;FA;;;' + $ownerSid.Value + ')(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)'),
        [Security.AccessControl.AccessControlSections]::Access)
    # Change only the DACL. Set-Acl may also attempt a SACL write requiring SeSecurityPrivilege.
    if ($PSVersionTable.PSEdition -eq 'Core') {
        [IO.FileSystemAclExtensions]::SetAccessControl([IO.DirectoryInfo]::new($DataDirectory), $directoryAcl)
    } else {
        [IO.Directory]::SetAccessControl($DataDirectory, $directoryAcl)
    }

    $caddyLock = Get-Content (Join-Path $PSScriptRoot 'caddy-windows.json') -Raw | ConvertFrom-Json
    $toolDirectory = Join-Path $repoDirectory ".tools/caddy/$($caddyLock.version)"
    New-Item -ItemType Directory -Path $toolDirectory -Force | Out-Null
    $archivePath = Join-Path $toolDirectory "caddy_$($caddyLock.version)_windows_amd64.zip"
    $caddyPath = Join-Path $toolDirectory 'caddy.exe'
    if (-not (Test-Path -LiteralPath $caddyPath)) {
        Invoke-WebRequest "https://github.com/caddyserver/caddy/releases/download/v$($caddyLock.version)/caddy_$($caddyLock.version)_windows_amd64.zip" -OutFile $archivePath
        if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $caddyLock.archive_sha256) {
            throw 'Caddy archive SHA256 mismatch.'
        }
        Expand-Archive -LiteralPath $archivePath -DestinationPath $toolDirectory -Force
    }
    if ((Get-FileHash -LiteralPath $caddyPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $caddyLock.executable_sha256) {
        throw 'Caddy executable SHA256 mismatch; preserve the file and investigate.'
    }
    $proxyKeyPath = Join-Path $DataDirectory 'proxy.key'
    if (-not (Test-Path -LiteralPath $proxyKeyPath)) {
        $proxyBytes = [byte[]]::new(32)
        $proxyRandom = [Security.Cryptography.RandomNumberGenerator]::Create()
        try { $proxyRandom.GetBytes($proxyBytes) } finally { $proxyRandom.Dispose() }
        [IO.File]::WriteAllText($proxyKeyPath, [Convert]::ToBase64String($proxyBytes).TrimEnd('=').Replace('+','-').Replace('/','_'), [Text.Encoding]::ASCII)
    }
    $proxyKeyValue = [IO.File]::ReadAllText($proxyKeyPath, [Text.Encoding]::ASCII).Trim()
    if ($proxyKeyValue -notmatch '^[A-Za-z0-9_-]{32,}$') { throw 'Invalid proxy key file; preserve it and inspect configuration.' }
    $deployment = [ordered]@{
        repository = $repoDirectory; python = (Get-Command python).Source; caddy = $caddyPath
        data_directory = $DataDirectory; database = (Join-Path $DataDirectory 'team.sqlite3')
        address = $Address; protocol = $Protocol.ToLowerInvariant(); web_port = $WebPort; backend_port = $BackendPort
        allow_insecure_http = ($Protocol -eq 'Http')
        roster = (Join-Path $repoDirectory 'data/quiz-team-roster.json'); proxy_key_file = $proxyKeyPath
        public_url = "$($Protocol.ToLowerInvariant())://${Address}:$WebPort"
    }
    $deployment | ConvertTo-Json | Set-Content -LiteralPath $configPath -Encoding UTF8
    $storageDirectory = (Join-Path $DataDirectory 'tls').Replace('\', '/')
    $tlsOption = ''
    $globalOptions = 'auto_https off'
    if ($Protocol -eq 'Https') {
        $tlsOption = 'tls internal'
        $globalOptions = @"
    auto_https disable_redirects
    skip_install_trust
    storage file_system "$storageDirectory"
    pki {
        ca local {
            name "CSharp Quiz LAN"
        }
    }
"@
    }
    @"
{
    admin off
    persist_config off
    $globalOptions
    servers {
        protocols h1 h2
    }
}
$($deployment.public_url) {
    bind $Address
    $tlsOption
    reverse_proxy 127.0.0.1:$BackendPort {
        header_up X-Quiz-Proxy-Key "$proxyKeyValue"
        header_up X-Quiz-Client-IP {remote_host}
        header_up -X-Quiz-Domain-Account
        header_up -X-Quiz-Domain-SID
    }
}
"@ | Set-Content -LiteralPath (Join-Path $DataDirectory 'Caddyfile') -Encoding UTF8
    & $caddyPath validate --config (Join-Path $DataDirectory 'Caddyfile') --adapter caddyfile
    if ($LASTEXITCODE -ne 0) { throw 'Caddy configuration validation failed.' }
    & $deployment.python $hostScript --config $configPath --bootstrap
    if ($LASTEXITCODE -ne 0) { throw 'Account bootstrap failed; inspect the data directory before retrying.' }
    Write-Output "PASS: prepared $($deployment.public_url); data: $DataDirectory"
    exit 0
}

$deployment = Read-Deployment
$taskName = "CSharpQuizPublic-$($deployment.web_port)"
$taskExecutable = (Get-Command powershell.exe).Source
$taskArguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $PSCommandPath +
    '" -Action Run -DataDirectory "' + $DataDirectory + '"'
$pausePath = Join-Path $DataDirectory 'maintenance.pause'

function Get-QuizTask {
    $scheduled = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($scheduled -and ($scheduled.Actions.Count -ne 1 -or $scheduled.Actions[0].Execute -ne $taskExecutable -or
            $scheduled.Actions[0].Arguments -ne $taskArguments)) {
        throw "Scheduled task $taskName belongs to another deployment; no task was changed."
    }
    return $scheduled
}

function New-QuizTaskDefinition {
    $taskAction = New-ScheduledTaskAction -Execute $taskExecutable -Argument $taskArguments -WorkingDirectory $repoDirectory
    $bootTrigger = New-ScheduledTaskTrigger -AtStartup
    $retryTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew `
        -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    # Local files and listening sockets need no stored domain password or SYSTEM privileges.
    $directorySecurity = if ($PSVersionTable.PSEdition -eq 'Core') {
        [IO.FileSystemAclExtensions]::GetAccessControl([IO.DirectoryInfo]::new($DataDirectory))
    } else { [IO.Directory]::GetAccessControl($DataDirectory) }
    $ownerSid = $directorySecurity.GetOwner([Security.Principal.SecurityIdentifier]).Value
    $principal = New-ScheduledTaskPrincipal -UserId $ownerSid -LogonType S4U -RunLevel Limited
    return New-ScheduledTask -Action $taskAction -Trigger @($bootTrigger, $retryTrigger) -Settings $settings `
        -Principal $principal -Description 'C# quiz boot startup and recovery; Stop pauses recovery, Start resumes it.'
}

switch ($Action) {
    'DefaultAdmin' {
        & $deployment.python $hostScript --config $configPath --use-default-admin
        if ($LASTEXITCODE -ne 0) { throw 'Default administrator setup failed; preserve the data directory and inspect the error.' }
    }
    'Start' {
        if (Test-Path -LiteralPath $pausePath) { Remove-Item -LiteralPath $pausePath -Force }
        Add-Content -LiteralPath (Join-Path $DataDirectory 'operator-events.log') -Encoding UTF8 -Value (
            [DateTimeOffset]::Now.ToString('o') + ' START_REQUEST user=' + [Security.Principal.WindowsIdentity]::GetCurrent().Name)
        if (Get-QuizHost) { Write-Output 'PASS: deployment already running'; break }
        foreach ($listenPort in @($deployment.web_port, $deployment.backend_port)) {
            if (Get-NetTCPConnection -State Listen -LocalPort $listenPort -ErrorAction SilentlyContinue) {
                throw "Port $listenPort is already in use; no existing process was stopped."
            }
        }
        $scheduled = Get-QuizTask
        if ($scheduled) {
            if ($scheduled.State -eq 'Disabled') { Enable-ScheduledTask -InputObject $scheduled | Out-Null }
            Start-ScheduledTask -InputObject $scheduled
        } else {
            Start-Process -FilePath $deployment.python -ArgumentList @('-u', ('"' + $hostScript + '"'),
                '--config', ('"' + $configPath + '"')) -WorkingDirectory $repoDirectory -WindowStyle Hidden `
                -RedirectStandardOutput (Join-Path $DataDirectory 'host.log') -RedirectStandardError (Join-Path $DataDirectory 'host-error.log') | Out-Null
        }
        $ready = $false
        for ($waitCount = 0; $waitCount -lt 20; $waitCount++) {
            Start-Sleep -Seconds 1
            if ((Get-QuizHost) -and (Get-NetTCPConnection -State Listen -LocalPort $deployment.web_port -ErrorAction SilentlyContinue) -and
                (Get-NetTCPConnection -State Listen -LocalPort $deployment.backend_port -ErrorAction SilentlyContinue)) {
                $ready = $true; break
            }
        }
        if (-not $ready) { throw "Deployment did not start; read $DataDirectory/host-error.log and services.log." }
        Write-Output "PASS: listening at $($deployment.public_url); verify firewall and peer access."
        if ($deployment.protocol -eq 'http') { Write-Output 'HTTP uses no certificate; network traffic is unencrypted.' }
    }
    'Stop' {
        New-Item -ItemType File -Path $pausePath -Force | Out-Null
        Add-Content -LiteralPath (Join-Path $DataDirectory 'operator-events.log') -Encoding UTF8 -Value (
            [DateTimeOffset]::Now.ToString('o') + ' STOP_REQUEST user=' + [Security.Principal.WindowsIdentity]::GetCurrent().Name)
        $runningHost = Get-QuizHost
        $scheduled = Get-QuizTask
        if (-not $runningHost -and (-not $scheduled -or $scheduled.State -ne 'Running')) {
            Write-Output 'PASS: deployment already stopped'; break
        }
        New-Item -ItemType File -Path (Join-Path $DataDirectory 'stop.request') -Force | Out-Null
        for ($waitCount = 0; $waitCount -lt 30; $waitCount++) {
            if (-not (Get-QuizHost) -and (Get-QuizTask).State -ne 'Running') { break }
            Start-Sleep -Seconds 1
        }
        if ((Get-QuizHost) -or (Get-QuizTask).State -eq 'Running') {
            throw 'Supervisor did not stop; inspect logs. No unrelated PID was terminated.'
        }
        Write-Output 'PASS: stopped; accounts and reports preserved'
    }
    'Status' {
        Write-Output "URL: $($deployment.public_url)"
        Write-Output "Data: $DataDirectory"
        Write-Output "Supervisor running: $([bool](Get-QuizHost))"
        Write-Output "Logon startup: $(Test-Path -LiteralPath $startupPath)"
        $scheduled = Get-QuizTask
        Write-Output "Boot/recovery task: $(if ($scheduled) { $scheduled.State } else { 'not installed' })"
        Write-Output "Maintenance paused: $(Test-Path -LiteralPath $pausePath)"
        if ($scheduled) {
            $taskInformation = $scheduled | Get-ScheduledTaskInfo
            Write-Output "Task last run: $($taskInformation.LastRunTime); result: $($taskInformation.LastTaskResult)"
        }
        Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {
            $_.LocalPort -in $deployment.web_port, $deployment.backend_port
        } | Select-Object LocalAddress, LocalPort, OwningProcess
    }
    'Autostart' {
        if (Test-Path -LiteralPath $startupPath) { throw 'Startup entry already exists; inspect it rather than replacing it.' }
        $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($startupPath)
        $shortcut.TargetPath = (Get-Command powershell.exe).Source
        $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $PSCommandPath +
            '" -Action Start -DataDirectory "' + $DataDirectory + '"'
        $shortcut.WorkingDirectory = $repoDirectory
        $shortcut.WindowStyle = 7
        $shortcut.Save()
        Write-Output 'PASS: starts after this Windows user signs in; not a pre-logon Windows service'
    }
    'RemoveAutostart' {
        if (Test-Path -LiteralPath $startupPath) {
            $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($startupPath)
            if (-not $shortcut.Arguments.Contains($PSCommandPath) -or -not $shortcut.Arguments.Contains($DataDirectory)) {
                throw 'Startup entry belongs to another deployment; no file was removed.'
            }
            Remove-Item -LiteralPath $startupPath
        }
        Write-Output 'PASS: startup entry removed; service and data unaffected'
    }
    'Run' {
        if (Test-Path -LiteralPath $pausePath) { break }
        if (Get-QuizHost) { break }
        & $deployment.python -u $hostScript --config $configPath
        exit $LASTEXITCODE
    }
    'TaskDefinition' {
        [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
        $definition = New-QuizTaskDefinition
        [ordered]@{
            Principal = $definition.Principal | Select-Object UserId,LogonType,RunLevel
            Actions = @($definition.Actions | Select-Object Execute,Arguments,WorkingDirectory)
            Settings = $definition.Settings | Select-Object ExecutionTimeLimit,MultipleInstances,StartWhenAvailable,
                RestartCount,RestartInterval,StopIfGoingOnBatteries,DisallowStartIfOnBatteries
            Triggers = @($definition.Triggers | Select-Object @{Name='Type'; Expression={$_.CimClass.CimClassName}},
                StartBoundary,@{Name='Repetition'; Expression={$_.Repetition | Select-Object Interval,Duration}})
        } | ConvertTo-Json -Depth 5
    }
    'InstallTask' {
        $operatorIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
        if (-not ([Security.Principal.WindowsPrincipal]::new($operatorIdentity)).IsInRole(
                [Security.Principal.WindowsBuiltInRole]::Administrator)) {
            throw 'Run InstallTask in an elevated PowerShell; runtime uses the deployment user without storing a password.'
        }
        $null = Get-QuizTask
        if (Test-Path -LiteralPath $startupPath) {
            $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($startupPath)
            if (-not $shortcut.Arguments.Contains($PSCommandPath) -or -not $shortcut.Arguments.Contains($DataDirectory)) {
                throw 'Startup entry belongs to another deployment; no task or shortcut was changed.'
            }
        }
        Start-Transcript -Path (Join-Path $DataDirectory 'keepalive-install.log') -Append | Out-Null
        try {
            $definition = New-QuizTaskDefinition
            Register-ScheduledTask -TaskName $taskName -InputObject $definition -Force | Out-Null
            if (Test-Path -LiteralPath $startupPath) { Remove-Item -LiteralPath $startupPath }
            Write-Output "PASS: $taskName installed; starts without interactive logon; unlimited runtime; one-minute recovery"
        } finally { Stop-Transcript | Out-Null }
    }
    'RemoveTask' {
        if (Get-QuizHost) { throw 'Run Stop before removing the boot/recovery task.' }
        $scheduled = Get-QuizTask
        if ($scheduled) { Unregister-ScheduledTask -InputObject $scheduled -Confirm:$false }
        Write-Output 'PASS: boot/recovery task removed; database preserved'
    }
    'Trust' {
        if ($deployment.protocol -eq 'http') { Write-Output 'PASS: HTTP needs no certificate or trust import'; break }
        $certificatePath = Join-Path $DataDirectory 'tls/pki/authorities/local/root.crt'
        if (-not (Test-Path -LiteralPath $certificatePath)) { throw 'Run Prepare first to generate the CA certificate.' }
        $certificate = [Security.Cryptography.X509Certificates.X509Certificate2]::new($certificatePath)
        Import-Certificate -FilePath $certificatePath -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
        Copy-Item -LiteralPath $certificatePath -Destination (Join-Path $DataDirectory 'quiz-lan-root.crt')
        Write-Output "PASS: trusted for this Windows user only; SHA1 thumbprint: $($certificate.Thumbprint)"
        Write-Output 'Peers must verify and import quiz-lan-root.crt; never distribute root.key or tls/.'
    }
    'Firewall' {
        $isElevated = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
            [Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isElevated) { throw 'Administrator rights required only for this firewall action. Ask IT to run the documented command.' }
        $ruleName = "CSharpQuizPublic-$($deployment.protocol.ToUpperInvariant())-$($deployment.web_port)"
        $existingRule = Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
        if ($existingRule) {
            $portFilter = $existingRule | Get-NetFirewallPortFilter
            $addressFilter = $existingRule | Get-NetFirewallAddressFilter
            $applicationFilter = $existingRule | Get-NetFirewallApplicationFilter
            if ([int]$existingRule.Direction -eq 1 -and
                [int]$existingRule.Action -eq 2 -and [int]$existingRule.Profile -eq 3 -and
                $portFilter.Protocol -in 'TCP','6' -and $portFilter.LocalPort -eq [string]$deployment.web_port -and
                (@($addressFilter.LocalAddress) -join ',') -eq $deployment.address -and
                (@($addressFilter.RemoteAddress) -join ',') -eq 'LocalSubnet' -and $applicationFilter.Program -eq $deployment.caddy) {
                if ([int]$existingRule.Enabled -ne 1) { Enable-NetFirewallRule -Name $ruleName | Out-Null }
                Write-Output 'PASS: matching firewall rule enabled'
            } else {
                throw 'Named firewall rule has different settings; inspect its effective scope before changing it.'
            }
        } else {
            New-NetFirewallRule -Name $ruleName -DisplayName "CSharp Quiz $($deployment.protocol.ToUpperInvariant()) $($deployment.web_port)" -Direction Inbound `
                -Action Allow -Protocol TCP -LocalPort $deployment.web_port -LocalAddress $deployment.address `
                -Program $deployment.caddy -RemoteAddress LocalSubnet -Profile Domain,Private | Out-Null
        }
        # Windows may add broad application rules when its network prompt is accepted.
        # Restrict only auto-created rules for this exact deployment executable.
        $automaticRules = Get-NetFirewallApplicationFilter | Where-Object { $_.Program -eq $deployment.caddy } |
            Get-NetFirewallRule | Where-Object { [int]$_.Enabled -eq 1 -and [int]$_.Direction -eq 1 -and
                [int]$_.Action -eq 2 -and ($_.Name -like 'TCP Query User{*' -or $_.Name -like 'UDP Query User{*') }
        foreach ($automaticRule in $automaticRules) {
            Disable-NetFirewallRule -Name $automaticRule.Name | Out-Null
            Write-Output "Disabled broad Windows application rule for this deployment: $($automaticRule.Name)"
        }
        # Retire only previously managed ports for this same executable and local address.
        $previousRules = Get-NetFirewallApplicationFilter | Where-Object { $_.Program -eq $deployment.caddy } |
            Get-NetFirewallRule | Where-Object { [int]$_.Enabled -eq 1 -and $_.Name -ne $ruleName -and
                ($_.Name -like 'CSharpQuizPublic-HTTP-*' -or $_.Name -like 'CSharpQuizPublic-HTTPS-*') }
        foreach ($previousRule in $previousRules) {
            $previousAddress = $previousRule | Get-NetFirewallAddressFilter
            if ((@($previousAddress.LocalAddress) -join ',') -eq $deployment.address) {
                Disable-NetFirewallRule -Name $previousRule.Name | Out-Null
                Write-Output "Disabled previous deployment port: $($previousRule.Name)"
            }
        }
        Write-Output 'PASS: one web TCP port allowed from local subnets on Domain/Private profiles; verify from another machine.'
    }
}
