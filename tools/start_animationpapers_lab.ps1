param(
    [int]$Port = 8891,
    [switch]$NoOpen,
    [switch]$ForceVerify,
    [switch]$NoReuseServer
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $PSScriptRoot "cases.yaml"
$runCasePath = Join-Path $PSScriptRoot "run_case.ps1"
$prepareAssetsPath = Join-Path $PSScriptRoot "prepare_assets.ps1"
$reportsRoot = Join-Path $repoRoot ".reports"
$logsDir = Join-Path $reportsRoot "logs"
$studyAnimationPapersDir = Join-Path $reportsRoot "study\AnimationPapers"
$localJupyterRoot = Join-Path $repoRoot ".jupyter"
$localJupyterConfig = Join-Path $localJupyterRoot "config"
$localJupyterPath = Join-Path $localJupyterRoot "share\jupyter"
$localJupyterRuntime = Join-Path $repoRoot ".jupyter-runtime"
$launcherEnv = Join-Path $repoRoot ".envs\motion_matching"
$launcherPython = Join-Path $launcherEnv "python.exe"
$studyUrlPath = ".reports/study/AnimationPapers"

New-Item -ItemType Directory -Force -Path $reportsRoot, $logsDir, $studyAnimationPapersDir, $localJupyterRoot, $localJupyterConfig, $localJupyterPath, $localJupyterRuntime | Out-Null

$env:JUPYTER_CONFIG_DIR = $localJupyterConfig
$env:JUPYTER_DATA_DIR = $localJupyterRoot
$env:JUPYTER_PATH = $localJupyterPath
$env:IPYTHONDIR = Join-Path $localJupyterRoot "ipython"
$env:JUPYTER_RUNTIME_DIR = $localJupyterRuntime
New-Item -ItemType Directory -Force -Path $env:IPYTHONDIR | Out-Null

function Read-Manifest {
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        throw "Manifest missing: $manifestPath"
    }
    return Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Get-AnimationPapersCases {
    $manifest = Read-Manifest
    return @($manifest.cases | Where-Object {
        ([string]$_.entry).Replace("\", "/").StartsWith("labs/AnimationPapers/")
    })
}

function Get-CaseBySlug([string]$slug) {
    $manifest = Read-Manifest
    return $manifest.cases | Where-Object { $_.slug -eq $slug } | Select-Object -First 1
}

function Get-CaseStatus($case) {
    if ($null -eq $case.status_policy) {
        return ""
    }
    if ($case.status_policy.PSObject.Properties.Name -contains "current_status") {
        return [string]$case.status_policy.current_status
    }
    return ""
}

function Test-NotebookKind($case) {
    return ([string]$case.kind -eq "notebook") -and ([IO.Path]::GetExtension([string]$case.entry).ToLowerInvariant() -eq ".ipynb")
}

function Get-StudyNotebookPath($case) {
    return Join-Path $studyAnimationPapersDir ([IO.Path]::GetFileName([string]$case.entry))
}

function Test-StudyNotebook($case, [ref]$reason) {
    if (-not (Test-NotebookKind $case)) {
        return $true
    }

    $studyPath = Get-StudyNotebookPath $case
    if (-not (Test-Path -LiteralPath $studyPath)) {
        $reason.Value = "missing study notebook: $studyPath"
        return $false
    }

    try {
        $notebook = Get-Content -LiteralPath $studyPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $kernelName = ""
        if ($null -ne $notebook.metadata -and $null -ne $notebook.metadata.kernelspec) {
            $kernelName = [string]$notebook.metadata.kernelspec.name
        }
        if ($kernelName -ne [string]$case.kernel_name) {
            $reason.Value = "study notebook kernel mismatch: $kernelName != $($case.kernel_name)"
            return $false
        }

        foreach ($cell in @($notebook.cells)) {
            if ([string]$cell.cell_type -ne "code") {
                continue
            }
            foreach ($output in @($cell.outputs)) {
                if ([string]$output.output_type -eq "error") {
                    $reason.Value = "study notebook has saved error output: $studyPath"
                    return $false
                }
            }
        }
    }
    catch {
        $reason.Value = "study notebook is not readable JSON: $studyPath"
        return $false
    }

    return $true
}

function Test-KernelSpec($case, [ref]$reason) {
    if (-not (Test-NotebookKind $case)) {
        return $true
    }

    $kernelJson = Join-Path $localJupyterPath ("kernels\{0}\kernel.json" -f $case.kernel_name)
    if (-not (Test-Path -LiteralPath $kernelJson)) {
        $reason.Value = "missing kernelspec: $($case.kernel_name)"
        return $false
    }
    return $true
}

function Test-CaseReady($case, [ref]$reasons) {
    $caseReasons = @()
    $envPrefix = Join-Path $repoRoot ([string]$case.env_prefix)
    $pythonExe = Join-Path $envPrefix "python.exe"
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        $caseReasons += "missing env python: $pythonExe"
    }

    if ((Get-CaseStatus $case) -ne "passed") {
        $caseReasons += "status is not passed: $(Get-CaseStatus $case)"
    }

    $reason = ""
    if (-not (Test-KernelSpec $case ([ref]$reason))) {
        $caseReasons += $reason
    }

    $reason = ""
    if (-not (Test-StudyNotebook $case ([ref]$reason))) {
        $caseReasons += $reason
    }

    $reasons.Value = $caseReasons
    return $caseReasons.Count -eq 0
}

function Invoke-RunCase([string]$slug) {
    Write-Host "Preparing case: $slug"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $runCasePath -Slug $slug
    if ($LASTEXITCODE -ne 0) {
        throw "run_case.ps1 failed for $slug with exit code $LASTEXITCODE"
    }
}

function Ensure-LauncherEnv {
    if (Test-Path -LiteralPath $launcherPython) {
        return
    }

    Write-Host "Launcher environment is missing. Preparing motion_matching first..."
    Invoke-RunCase "motion_matching"
    if (-not (Test-Path -LiteralPath $launcherPython)) {
        throw "Launcher python is still missing after motion_matching: $launcherPython"
    }
}

function Get-FreePort([int]$startPort) {
    $candidate = $startPort
    while ($candidate -lt ($startPort + 100)) {
        $listener = Get-NetTCPConnection -State Listen -LocalPort $candidate -ErrorAction SilentlyContinue
        if ($null -eq $listener) {
            return $candidate
        }
        $candidate += 1
    }
    throw "No free TCP port found from $startPort to $($startPort + 99)"
}

function Get-LiveJupyterServers {
    $servers = @()
    if (-not (Test-Path -LiteralPath $localJupyterRuntime)) {
        return $servers
    }

    foreach ($runtimeFile in Get-ChildItem -LiteralPath $localJupyterRuntime -Filter "jpserver-*.json" -ErrorAction SilentlyContinue) {
        try {
            $info = Get-Content -LiteralPath $runtimeFile.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            $token = [string]$info.token
            $url = ([string]$info.url).TrimEnd("/")
            $statusUrl = "{0}/api/status?token={1}" -f $url, [uri]::EscapeDataString($token)
            Invoke-RestMethod -Uri $statusUrl -TimeoutSec 5 | Out-Null
            $servers += [pscustomobject]@{
                pid = [int]$info.pid
                port = [int]$info.port
                url = $url
                token = $token
                root_dir = [string]$info.root_dir
                runtime_file = $runtimeFile.FullName
            }
        }
        catch {
        }
    }
    return @($servers | Sort-Object -Property @{ Expression = { $_.pid -eq 0 } }, @{ Expression = { $_.runtime_file } } -Descending)
}

function Stop-LauncherServers {
    $ports = 8888..8999
    foreach ($listener in @(Get-NetTCPConnection -State Listen -LocalPort $ports -ErrorAction SilentlyContinue)) {
        $proc = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        if ($null -ne $proc -and $proc.Path -eq $launcherPython) {
            Write-Host "Stopping existing AnimationPapers JupyterLab pid=$($proc.Id) port=$($listener.LocalPort)"
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

function Start-JupyterLab([int]$requestedPort) {
    if ($NoReuseServer) {
        Stop-LauncherServers
        Start-Sleep -Seconds 1
    }
    else {
        $servers = @(Get-LiveJupyterServers | Where-Object { $_.root_dir -eq $repoRoot })
        foreach ($server in $servers) {
            $proc = Get-Process -Id $server.pid -ErrorAction SilentlyContinue
            if ($null -ne $proc -and $proc.Path -eq $launcherPython) {
                Write-Host "Reusing JupyterLab pid=$($server.pid) port=$($server.port)"
                return $server
            }
        }
    }

    $selectedPort = Get-FreePort $requestedPort
    $stdoutLog = Join-Path $logsDir ("jupyterlab_animationpapers_{0}.log" -f $selectedPort)
    $stderrLog = Join-Path $logsDir ("jupyterlab_animationpapers_{0}.stderr.log" -f $selectedPort)
    Remove-Item -LiteralPath $stdoutLog, $stderrLog -ErrorAction SilentlyContinue

    $args = @(
        "-m", "jupyter", "lab",
        "--no-browser",
        "--ip=127.0.0.1",
        "--port=$selectedPort",
        "--ServerApp.port_retries=0",
        "--notebook-dir=$repoRoot",
        "--ContentsManager.allow_hidden=True",
        "--LabApp.default_url=/lab/workspaces/animationtech-study/tree/$studyUrlPath"
    )

    $proc = Start-Process -FilePath $launcherPython -ArgumentList $args -WorkingDirectory $repoRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
    Write-Host "Started JupyterLab pid=$($proc.Id) port=$selectedPort"

    $deadline = (Get-Date).AddSeconds(45)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 800
        $server = @(Get-LiveJupyterServers | Where-Object { $_.pid -eq $proc.Id } | Select-Object -First 1)
        if ($server.Count -gt 0) {
            $server | Add-Member -NotePropertyName stdout_log -NotePropertyValue $stdoutLog -Force
            $server | Add-Member -NotePropertyName stderr_log -NotePropertyValue $stderrLog -Force
            return $server
        }
    }

    throw "JupyterLab did not become ready within 45 seconds. Check $stderrLog"
}

function Test-ServerReady($server, $notebookCases) {
    $baseUrl = ([string]$server.url).TrimEnd("/")
    $token = [string]$server.token
    $contentPath = [uri]::EscapeDataString("$studyUrlPath/Near-optimal Character Animation with Continuous Control.ipynb")
    $contentUrl = "{0}/api/contents/{1}?token={2}" -f $baseUrl, $contentPath, [uri]::EscapeDataString($token)
    Invoke-RestMethod -Uri $contentUrl -TimeoutSec 15 | Out-Null

    $kernelUrl = "{0}/api/kernelspecs?token={1}" -f $baseUrl, [uri]::EscapeDataString($token)
    $kernels = Invoke-RestMethod -Uri $kernelUrl -TimeoutSec 15
    $missing = @()
    foreach ($case in $notebookCases) {
        if (-not ($kernels.kernelspecs.PSObject.Properties.Name -contains [string]$case.kernel_name)) {
            $missing += [string]$case.kernel_name
        }
    }
    if ($missing.Count -gt 0) {
        throw "JupyterLab is missing kernelspecs: $($missing -join ', ')"
    }
}

if (-not (Test-Path -LiteralPath $runCasePath)) {
    throw "run_case.ps1 missing: $runCasePath"
}

$cases = @(Get-AnimationPapersCases)
if ($cases.Count -eq 0) {
    throw "No AnimationPapers cases found in $manifestPath"
}
$notebookCases = @($cases | Where-Object { Test-NotebookKind $_ })

Ensure-LauncherEnv

$casesToRun = New-Object System.Collections.Generic.List[string]
foreach ($case in $cases) {
    $reasons = @()
    $ready = Test-CaseReady $case ([ref]$reasons)
    if ($ForceVerify -or -not $ready) {
        $casesToRun.Add([string]$case.slug)
        if ($ForceVerify) {
            Write-Host "Will verify $($case.slug): ForceVerify"
        }
        else {
            Write-Host "Will prepare $($case.slug): $($reasons -join '; ')"
        }
    }
}

if ($casesToRun.Count -gt 0 -and (Test-Path -LiteralPath $prepareAssetsPath)) {
    Write-Host "Preparing shared public assets..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File $prepareAssetsPath
    if ($LASTEXITCODE -ne 0) {
        throw "prepare_assets.ps1 failed with exit code $LASTEXITCODE"
    }
}

foreach ($slug in $casesToRun) {
    Invoke-RunCase $slug
}

$refreshedCases = @(Get-AnimationPapersCases)
$remainingFailures = @()
foreach ($case in $refreshedCases) {
    $reasons = @()
    if (-not (Test-CaseReady $case ([ref]$reasons))) {
        $remainingFailures += ("{0}: {1}" -f $case.slug, ($reasons -join "; "))
    }
}
if ($remainingFailures.Count -gt 0) {
    Write-Error "AnimationPapers environment is not complete:`n$($remainingFailures -join "`n")"
    exit 1
}

$server = Start-JupyterLab -requestedPort $Port
Test-ServerReady -server $server -notebookCases $notebookCases

$finalUrl = "{0}/lab/workspaces/animationtech-study/tree/{1}?token={2}" -f ([string]$server.url).TrimEnd("/"), $studyUrlPath, [uri]::EscapeDataString([string]$server.token)

Write-Host ""
Write-Host "AnimationPapers JupyterLab is ready."
Write-Host "URL: $finalUrl"
Write-Host "PID: $($server.pid)"
Write-Host "Port: $($server.port)"
if ($server.PSObject.Properties.Name -contains "stdout_log") {
    Write-Host "Log: $($server.stdout_log)"
    Write-Host "Err: $($server.stderr_log)"
}

if (-not $NoOpen) {
    Start-Process $finalUrl
}
