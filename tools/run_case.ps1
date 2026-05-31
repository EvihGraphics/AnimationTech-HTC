param(
    [Parameter(Mandatory = $true)]
    [string]$Slug,
    [ValidateSet("auto", "validate", "adaptive", "quality")]
    [string]$TrainingProfile = "auto",
    [ValidateSet("auto", "cpu", "gpu")]
    [string]$TorchDevice = "auto",
    [Nullable[int]]$MaxWorkers,
    [Nullable[int]]$GpuIndex
)

$ErrorActionPreference = "Continue"

$repoRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $PSScriptRoot "cases.yaml"
$prepareAssetsPath = Join-Path $PSScriptRoot "prepare_assets.ps1"
$prepareNotebookPath = Join-Path $PSScriptRoot "prepare_notebook.py"
$haloFaceAssetPath = Join-Path $PSScriptRoot "generate_halo_face_asset.py"
$reportsRoot = Join-Path $repoRoot ".reports"
$logsDir = Join-Path $reportsRoot "logs"
$executedDir = Join-Path $reportsRoot "executed"
$preparedDir = Join-Path $reportsRoot "prepared"
$studyRoot = Join-Path $reportsRoot "study"
$studyAnimationPapersDir = Join-Path $studyRoot "AnimationPapers"
$locksDir = Join-Path $reportsRoot "locks"
$statusDir = Join-Path $reportsRoot "status"
$localJupyterRoot = Join-Path $repoRoot ".jupyter"
$localJupyterConfig = Join-Path $localJupyterRoot "config"
$localJupyterPath = Join-Path $localJupyterRoot "share\jupyter"

New-Item -ItemType Directory -Force -Path $reportsRoot, $logsDir, $executedDir, $preparedDir, $studyRoot, $locksDir, $statusDir, $localJupyterRoot, $localJupyterConfig, $localJupyterPath | Out-Null

$env:JUPYTER_CONFIG_DIR = $localJupyterConfig
$env:JUPYTER_DATA_DIR = $localJupyterRoot
$env:JUPYTER_PATH = $localJupyterPath
$env:IPYTHONDIR = Join-Path $localJupyterRoot "ipython"
$env:PYTHONUTF8 = "1"
New-Item -ItemType Directory -Force -Path $env:IPYTHONDIR | Out-Null

function Get-LogicalProcessorCount {
    try {
        $count = (Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
        if ($count) {
            return [int]$count
        }
    }
    catch {
    }
    return [Environment]::ProcessorCount
}

function Get-NvidiaGpuInfo {
    $command = Get-Command "nvidia-smi.exe" -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        $command = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
    }
    if ($null -eq $command) {
        return @()
    }

    $output = & $command.Source --query-gpu=index,name,memory.free,memory.total,utilization.gpu,display_active --format=csv,noheader,nounits 2>$null
    if ($LASTEXITCODE -ne 0 -or $null -eq $output) {
        return @()
    }

    $gpus = @()
    foreach ($line in @($output)) {
        $parts = $line -split "," | ForEach-Object { $_.Trim() }
        if ($parts.Count -lt 6) {
            continue
        }
        $gpus += [pscustomobject]@{
            index = [int]$parts[0]
            name = $parts[1]
            memory_free_mb = [int]$parts[2]
            memory_total_mb = [int]$parts[3]
            utilization_gpu = [int]$parts[4]
            display_active = $parts[5]
        }
    }
    return $gpus
}

function Select-BestGpu($gpus) {
    if ($null -eq $gpus -or $gpus.Count -eq 0) {
        return $null
    }

    return $gpus |
        Sort-Object `
            @{ Expression = { if ($_.display_active -match "Disabled|Off|False|0") { 0 } else { 1 } } }, `
            @{ Expression = { -1 * [int]$_.memory_free_mb } }, `
            @{ Expression = { [int]$_.utilization_gpu } } |
        Select-Object -First 1
}

function Get-CaseTrainingProfile([string]$caseSlug, [string]$requestedProfile) {
    if ($requestedProfile -ne "auto") {
        return $requestedProfile
    }

    switch ($caseSlug) {
        "motion_fields_for_interactive_character_animation" { return "adaptive" }
        "real_time_planning_for_parameterized_human_motion" { return "adaptive" }
        "knowing_when_to_put_your_foot_down" { return "adaptive" }
        default { return "validate" }
    }
}

function Get-RecommendedMaxWorkers([string]$resolvedProfile, [Nullable[int]]$requestedMaxWorkers) {
    if ($requestedMaxWorkers) {
        return [int]$requestedMaxWorkers
    }

    $logicalCount = Get-LogicalProcessorCount
    $scale = switch ($resolvedProfile) {
        "quality" { 0.75 }
        "adaptive" { 0.50 }
        default { 0.375 }
    }

    $recommended = [math]::Floor($logicalCount * $scale)
    $recommended = [math]::Max(4, $recommended)
    $recommended = [math]::Min(12, $recommended)
    return [int]$recommended
}

function Get-RecommendedTreeJobs([int]$resolvedMaxWorkers) {
    if ($resolvedMaxWorkers -ge 12) {
        return 2
    }
    return 1
}

function Resolve-ExecutionResources([string]$caseSlug, [string]$templateName, [string]$requestedProfile, [string]$requestedTorchDevice, [Nullable[int]]$requestedMaxWorkers, [Nullable[int]]$requestedGpuIndex) {
    $resolvedProfile = Get-CaseTrainingProfile -caseSlug $caseSlug -requestedProfile $requestedProfile
    $resolvedMaxWorkers = Get-RecommendedMaxWorkers -resolvedProfile $resolvedProfile -requestedMaxWorkers $requestedMaxWorkers
    $resolvedTreeJobs = Get-RecommendedTreeJobs -resolvedMaxWorkers $resolvedMaxWorkers
    $gpus = @(Get-NvidiaGpuInfo)
    $selectedGpu = $null
    $resolvedTorchDevice = "cpu"

    if ($requestedGpuIndex -ne $null) {
        $selectedGpu = $gpus | Where-Object { $_.index -eq [int]$requestedGpuIndex } | Select-Object -First 1
        if ($null -eq $selectedGpu) {
            throw "Requested GPU index $requestedGpuIndex was not detected."
        }
    }

    if ($requestedTorchDevice -eq "cpu") {
        $resolvedTorchDevice = "cpu"
    }
    elseif ($requestedTorchDevice -eq "gpu") {
        if ($null -eq $selectedGpu) {
            $selectedGpu = Select-BestGpu -gpus $gpus
        }
        if ($null -eq $selectedGpu) {
            throw "GPU execution was requested, but no NVIDIA GPU was detected."
        }
        $resolvedTorchDevice = "cuda"
    }
    elseif ($caseSlug -eq "motion_fields_for_interactive_character_animation") {
        $resolvedTorchDevice = "cpu"
    }
    elseif ($templateName -eq "papers-torch") {
        if ($null -eq $selectedGpu) {
            $selectedGpu = Select-BestGpu -gpus $gpus
        }
        if ($null -ne $selectedGpu) {
            $resolvedTorchDevice = "cuda"
        }
    }

    return [pscustomobject]@{
        training_profile = $resolvedProfile
        torch_device = $resolvedTorchDevice
        selected_gpu = $selectedGpu
        max_workers = $resolvedMaxWorkers
        tree_jobs = $resolvedTreeJobs
    }
}

function Load-Manifest {
    return Get-Content -Path $manifestPath -Raw | ConvertFrom-Json
}

function Save-Manifest($manifest) {
    $content = $manifest | ConvertTo-Json -Depth 16
    Set-Content -Path $manifestPath -Value ($content + "`n") -Encoding UTF8
}

function Get-CasePathValue($item) {
    if ($item -is [string]) {
        return $item
    }
    if ($null -ne $item -and $item.PSObject.Properties.Name -contains "path") {
        return [string]$item.path
    }
    return $null
}

function Get-AssetId($item) {
    if ($item -is [string]) {
        return $item
    }
    if ($null -ne $item -and $item.PSObject.Properties.Name -contains "id") {
        return [string]$item.id
    }
    return $null
}

function Get-StatusObject($case, $status, $note) {
    $existing = @{}
    if ($null -ne $case.status_policy) {
        $case.status_policy.PSObject.Properties | ForEach-Object {
            $existing[$_.Name] = $_.Value
        }
    }
    $existing["current_status"] = $status
    $existing["last_run_utc"] = (Get-Date).ToUniversalTime().ToString("o")
    if ($note) {
        $existing["last_note"] = $note
    }
    return [pscustomobject]$existing
}

function Update-CaseStatus([string]$status, [string]$note) {
    $manifest = Load-Manifest
    $case = $manifest.cases | Where-Object { $_.slug -eq $Slug } | Select-Object -First 1
    if ($null -eq $case) {
        throw "Case $Slug not found while updating status."
    }
    $case.status_policy = Get-StatusObject -case $case -status $status -note $note
    Save-Manifest -manifest $manifest

    $statusFile = Join-Path $statusDir "$Slug.json"
    $payload = [pscustomobject]@{
        slug = $Slug
        status = $status
        note = $note
        updated_utc = $case.status_policy.last_run_utc
    }
    Set-Content -Path $statusFile -Value (($payload | ConvertTo-Json -Depth 8) + "`n") -Encoding UTF8
}

function Ensure-CondaEnv([string]$envPrefix, [string]$templatePath, [string]$kernelName, [string]$displayName, [string]$PythonVersion = "3.10", [bool]$RegisterKernel = $true) {
    $pythonExe = Join-Path $envPrefix "python.exe"
    if (-not (Test-Path $pythonExe)) {
        $created = $false
        for ($attempt = 1; $attempt -le 2; $attempt++) {
            if (Test-Path $envPrefix) {
                Remove-Item -Path $envPrefix -Recurse -Force -ErrorAction SilentlyContinue
            }

            & conda.exe create -y -p $envPrefix "python=$PythonVersion" pip
            if ($LASTEXITCODE -eq 0) {
                $created = $true
                break
            }

            if ($attempt -eq 1) {
                & conda.exe clean --packages --tarballs -y
            }
        }

        if (-not $created) {
            throw "Failed to create conda environment at $envPrefix after retrying conda cache cleanup."
        }
    }

    $templateHash = (Get-FileHash -Path $templatePath -Algorithm SHA256).Hash
    $templateStamp = Join-Path $envPrefix ".template-sha256"
    $currentHash = if (Test-Path $templateStamp) { (Get-Content -Path $templateStamp -Raw).Trim() } else { "" }

    if ($templateHash -ne $currentHash) {
        & $pythonExe -m pip install --disable-pip-version-check --no-warn-script-location --upgrade pip wheel
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to upgrade pip in $envPrefix"
        }

        & $pythonExe -m pip install --disable-pip-version-check --no-warn-script-location -r $templatePath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install template requirements from $templatePath"
        }

        Set-Content -Path $templateStamp -Value ($templateHash + "`n") -Encoding ASCII
    }

    if ($RegisterKernel) {
        $kernelDir = Join-Path $localJupyterPath "kernels\$kernelName"
        if (-not (Test-Path $kernelDir)) {
            & $pythonExe -m ipykernel install --prefix $localJupyterRoot --name $kernelName --display-name $displayName
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to register Jupyter kernel $kernelName"
            }
        }
    }
}

function Get-TorchRuntimeInfo([string]$pythonExe) {
    $probe = @'
import json
payload = {
    "import_ok": False,
    "cuda_available": False,
    "version": None,
    "cuda_version": None,
}
try:
    import torch
    payload["import_ok"] = True
    payload["cuda_available"] = bool(torch.cuda.is_available())
    payload["version"] = torch.__version__
    payload["cuda_version"] = torch.version.cuda
except Exception as exc:
    payload["error"] = str(exc)
print(json.dumps(payload))
'@
    $result = $probe | & $pythonExe -
    if ($LASTEXITCODE -ne 0 -or -not $result) {
        return $null
    }
    return $result | ConvertFrom-Json
}

function Ensure-TorchRuntime([string]$pythonExe, [string]$resolvedTorchDevice) {
    if ($resolvedTorchDevice -ne "cuda") {
        return
    }

    $runtimeInfo = Get-TorchRuntimeInfo -pythonExe $pythonExe
    if ($null -ne $runtimeInfo -and $runtimeInfo.import_ok -and $runtimeInfo.cuda_available) {
        return
    }

    & $pythonExe -m pip install --disable-pip-version-check --no-warn-script-location --upgrade --index-url https://download.pytorch.org/whl/cu128 torch torchvision torchaudio
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install CUDA-enabled PyTorch runtime."
    }

    $runtimeInfo = Get-TorchRuntimeInfo -pythonExe $pythonExe
    if ($null -eq $runtimeInfo -or -not $runtimeInfo.import_ok -or -not $runtimeInfo.cuda_available) {
        throw "CUDA-enabled PyTorch runtime is still unavailable after reinstall."
    }
}

function Write-LockFile([string]$envPrefix, [string]$lockPath) {
    $pythonExe = Join-Path $envPrefix "python.exe"
    $version = & $pythonExe -c "import sys; print(sys.version)"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to query Python version for $envPrefix"
    }

    Set-Content -Path $lockPath -Value ($version + "`n") -Encoding UTF8
    & $pythonExe -m pip freeze | Add-Content -Path $lockPath -Encoding UTF8
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to write lock file at $lockPath"
    }
}

function Test-ArtifactsExist($artifacts, [string]$sourceDir) {
    if ($null -eq $artifacts -or $artifacts.Count -eq 0) {
        return $true
    }

    foreach ($artifact in $artifacts) {
        $relativePath = Get-CasePathValue -item $artifact
        if (-not $relativePath) {
            continue
        }
        $repoRelativePath = Join-Path $repoRoot $relativePath
        $sourceRelativePath = Join-Path $sourceDir $relativePath
        if ((Test-Path $repoRelativePath) -or (Test-Path $sourceRelativePath)) {
            continue
        }
        else {
            return $false
        }
    }
    return $true
}

function Prepare-NotebookCopy([string]$envPrefix, [string]$entryPath, [string]$outputPath, [string]$ResolvedTrainingProfile, [string]$ResolvedTorchDevice, [string]$KernelName, [string]$DisplayName, [switch]$EnablePrecompute, [switch]$ClearOutputs) {
    $pythonExe = Join-Path $envPrefix "python.exe"
    $notebookWorkingDirectory = Split-Path -Parent $entryPath
    $args = @(
        $prepareNotebookPath,
        "--slug", $Slug,
        "--input", $entryPath,
        "--output", $outputPath,
        "--training-profile", $ResolvedTrainingProfile,
        "--torch-device", $ResolvedTorchDevice,
        "--kernel-name", $KernelName,
        "--display-name", $DisplayName,
        "--working-directory", $notebookWorkingDirectory
    )
    if ($EnablePrecompute) {
        $args += "--enable-precompute"
    }
    if ($ClearOutputs) {
        $args += "--clear-outputs"
    }

    & $pythonExe @args
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to prepare execution notebook for $Slug"
    }
}

function Copy-StudyNotebook([string]$entryPath, [string]$preparedPath) {
    if (-not (Test-Path $preparedPath)) {
        return
    }

    $animationPapersRoot = Join-Path $repoRoot "labs\AnimationPapers"
    $resolvedEntry = (Resolve-Path -LiteralPath $entryPath).Path
    $resolvedRoot = (Resolve-Path -LiteralPath $animationPapersRoot).Path
    if (-not $resolvedEntry.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return
    }

    New-Item -ItemType Directory -Force -Path $studyAnimationPapersDir | Out-Null
    $studyPath = Join-Path $studyAnimationPapersDir ([IO.Path]::GetFileName($entryPath))
    Copy-Item -LiteralPath $preparedPath -Destination $studyPath -Force
}

function Ensure-HaloFaceAsset([string]$pythonExe, [string]$outputPath) {
    & $pythonExe $haloFaceAssetPath "--output" $outputPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to generate synthetic Halo 4 facial animation asset."
    }
}

function Invoke-LoggedProcess([string]$filePath, [string[]]$arguments, [string]$workingDirectory, [string]$logPath) {
    $stderrPath = $logPath + ".stderr"
    Remove-Item -Path $logPath, $stderrPath -Force -ErrorAction SilentlyContinue

    $process = Start-Process -FilePath $filePath -ArgumentList $arguments -WorkingDirectory $workingDirectory -Wait -NoNewWindow -PassThru -RedirectStandardOutput $logPath -RedirectStandardError $stderrPath

    if (Test-Path $stderrPath) {
        Get-Content -Path $stderrPath | Add-Content -Path $logPath
        Remove-Item -Path $stderrPath -Force -ErrorAction SilentlyContinue
    }

    return $process.ExitCode
}

$manifest = Load-Manifest
$case = $manifest.cases | Where-Object { $_.slug -eq $Slug } | Select-Object -First 1
if ($null -eq $case) {
    throw "Case $Slug not found in $manifestPath"
}

$entryPath = Join-Path $repoRoot $case.entry
$sourceDir = Split-Path -Parent $entryPath
$template = [string]$case.template
$pythonVersion = if ($null -ne $case -and $case.PSObject.Properties.Name -contains "python_version" -and $case.python_version) { [string]$case.python_version } else { "3.10" }
$validationMode = [string]$case.validation_mode
$statusPolicyName = if ($null -ne $case.status_policy -and $case.status_policy.PSObject.Properties.Name -contains "policy") { [string]$case.status_policy.policy } else { "" }
$logPath = Join-Path $logsDir "$Slug.log"
$lockPath = Join-Path $locksDir "$Slug.txt"
$preparedPath = if ([string]$case.kind -eq "notebook") { Join-Path $sourceDir (".animationtech_prepared_" + $Slug + ".ipynb") } else { Join-Path $preparedDir "$Slug.ipynb" }
$caseExecutedDir = Join-Path $executedDir $Slug
$displayName = "AnimationTech ($Slug)"

if (($template -eq "blocked_external") -or ($template -eq "maya-external") -or ($statusPolicyName -eq "blocked_external") -or ($statusPolicyName -eq "maya_external")) {
    $note = if ($case.status_policy.last_note) { [string]$case.status_policy.last_note } else { "External dependency not available for unattended local execution." }
    Update-CaseStatus -status "blocked_external" -note $note
    Write-Host "$Slug -> blocked_external"
    exit 0
}

if (-not (Test-Path $entryPath)) {
    Update-CaseStatus -status "failed" -note "Entry file not found: $entryPath"
    throw "Entry file not found: $entryPath"
}

try {
    $resolvedResources = Resolve-ExecutionResources -caseSlug $Slug -templateName $template -requestedProfile $TrainingProfile -requestedTorchDevice $TorchDevice -requestedMaxWorkers $MaxWorkers -requestedGpuIndex $GpuIndex
    $env:ANIMATIONTECH_TRAINING_PROFILE = $resolvedResources.training_profile
    $env:ANIMATIONTECH_TORCH_DEVICE = $resolvedResources.torch_device
    $env:ANIMATIONTECH_MAX_WORKERS = [string]$resolvedResources.max_workers
    $env:ANIMATIONTECH_TREE_N_JOBS = [string]$resolvedResources.tree_jobs
    if ($null -ne $resolvedResources.selected_gpu) {
        $env:CUDA_VISIBLE_DEVICES = [string]$resolvedResources.selected_gpu.index
        $env:ANIMATIONTECH_SELECTED_GPU = [string]$resolvedResources.selected_gpu.index
    }
    else {
        $env:CUDA_VISIBLE_DEVICES = ""
        $env:ANIMATIONTECH_SELECTED_GPU = ""
    }

    foreach ($asset in @($case.public_assets)) {
        $assetId = Get-AssetId -item $asset
        if ($assetId -eq "lafan1") {
            & $prepareAssetsPath
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to prepare public asset lafan1."
            }
        }
    }

    $envPrefix = Join-Path $repoRoot $case.env_prefix
    $pythonExe = Join-Path $envPrefix "python.exe"
    $templatePath = Join-Path $PSScriptRoot ("templates\" + $template + ".txt")
    if (-not (Test-Path $templatePath)) {
        throw "Template requirements file missing: $templatePath"
    }

    Ensure-CondaEnv -envPrefix $envPrefix -templatePath $templatePath -kernelName $case.kernel_name -displayName $displayName -PythonVersion $pythonVersion -RegisterKernel:([string]$case.kind -eq "notebook")
    if ($template -eq "papers-torch") {
        Ensure-TorchRuntime -pythonExe $pythonExe -resolvedTorchDevice $resolvedResources.torch_device
    }
    foreach ($asset in @($case.public_assets)) {
        $assetId = Get-AssetId -item $asset
        if ($assetId -eq "halo_animated_face") {
            Ensure-HaloFaceAsset -pythonExe $pythonExe -outputPath (Join-Path $sourceDir "animated_face.dat")
        }
    }
    Write-LockFile -envPrefix $envPrefix -lockPath $lockPath
    New-Item -ItemType Directory -Force -Path $caseExecutedDir | Out-Null

    $artifactsPresent = Test-ArtifactsExist -artifacts @($case.generated_artifacts) -sourceDir $sourceDir
    $profileSpecificTrainingRun = (([string]$Slug -eq "motion_fields_for_interactive_character_animation") -or ([string]$Slug -eq "real_time_planning_for_parameterized_human_motion")) -and ($resolvedResources.training_profile -ne "validate")
    $needsPrecompute = (([string]$Slug -eq "motion_fields_for_interactive_character_animation") -or ([string]$Slug -eq "real_time_planning_for_parameterized_human_motion")) -and ((-not $artifactsPresent) -or $profileSpecificTrainingRun)

    if ([string]$case.kind -eq "notebook") {
        Prepare-NotebookCopy -envPrefix $envPrefix -entryPath $entryPath -outputPath $preparedPath -ResolvedTrainingProfile $resolvedResources.training_profile -ResolvedTorchDevice $resolvedResources.torch_device -KernelName $case.kernel_name -DisplayName $displayName -EnablePrecompute:$needsPrecompute -ClearOutputs

        $nbconvertExe = Join-Path $envPrefix "Scripts\jupyter-nbconvert.exe"
        $nbArgs = @(
            "--execute",
            "--to", "notebook",
            "--output", $Slug,
            "--output-dir", $caseExecutedDir,
            "--ExecutePreprocessor.timeout=-1",
            "--ExecutePreprocessor.kernel_name=$($case.kernel_name)",
            $preparedPath
        )
        if (Test-Path $nbconvertExe) {
            $exitCode = Invoke-LoggedProcess -filePath $nbconvertExe -arguments $nbArgs -workingDirectory $sourceDir -logPath $logPath
        }
        else {
            $exitCode = Invoke-LoggedProcess -filePath $pythonExe -arguments @("-m", "nbconvert") + $nbArgs -workingDirectory $sourceDir -logPath $logPath
        }
    }
    elseif ([string]$case.kind -eq "python_module") {
        if ([string]$Slug -eq "halo_4_exporter_from_maya") {
            $moduleArgs = @('"' + $entryPath + '"', "--output", (Join-Path $sourceDir "animated_face.dat"))
            $exitCode = Invoke-LoggedProcess -filePath $pythonExe -arguments $moduleArgs -workingDirectory $sourceDir -logPath $logPath
        }
        else {
            $moduleName = [IO.Path]::GetFileNameWithoutExtension($entryPath)
            $moduleCheckPath = Join-Path $preparedDir ($Slug + "_import_check.py")
            Set-Content -Path $moduleCheckPath -Value @(
                "import importlib"
                "import sys"
                "sys.path.insert(0, r'$sourceDir')"
                "importlib.import_module('$moduleName')"
            ) -Encoding ASCII
            $moduleArgs = @($moduleCheckPath)
            $exitCode = Invoke-LoggedProcess -filePath $pythonExe -arguments $moduleArgs -workingDirectory $sourceDir -logPath $logPath
        }
    }
    else {
        throw "Unsupported case kind: $($case.kind)"
    }
}
catch {
    $message = $_.Exception.Message
    if ($message -match "lafan1" -or $message -match "LFS" -or $message -match "over quota") {
        Update-CaseStatus -status "blocked_external" -note $message
        Write-Host "$Slug -> blocked_external"
        exit 0
    }

    Update-CaseStatus -status "failed" -note $message
    throw
}

if ($exitCode -ne 0) {
    Update-CaseStatus -status "failed" -note "Execution exited with code $exitCode. Check $logPath"
    exit $exitCode
}

if ([string]$case.kind -eq "notebook") {
    Copy-StudyNotebook -entryPath $entryPath -preparedPath $preparedPath
}

$note = if ($validationMode -match "manual_smoke") {
    "Automated execution passed. Manual JupyterLab smoke test is still required."
}
else {
    "Automated execution passed."
}

Update-CaseStatus -status "passed" -note $note
Write-Host "$Slug -> passed"
