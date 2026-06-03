param(
    [string[]]$Only
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $PSScriptRoot "cases.yaml"
$reportsRoot = Join-Path $repoRoot ".reports"
$summaryPath = Join-Path $reportsRoot "summary.json"
$runCasePath = Join-Path $PSScriptRoot "run_case.ps1"

New-Item -ItemType Directory -Force -Path $reportsRoot | Out-Null

$manifest = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json
$cases = @($manifest.cases)
if ($Only -and $Only.Count -gt 0) {
    $cases = $cases | Where-Object { $Only -contains $_.slug }
}

$results = @()
$hasFailure = $false

foreach ($case in $cases) {
    try {
        & $runCasePath -Slug $case.slug
    }
    catch {
        Write-Warning "$($case.slug) failed: $($_.Exception.Message)"
    }

    $updatedManifest = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json
    $updatedCase = $updatedManifest.cases | Where-Object { $_.slug -eq $case.slug } | Select-Object -First 1
    $currentStatus = if ($null -ne $updatedCase.status_policy -and $updatedCase.status_policy.PSObject.Properties.Name -contains "current_status") { [string]$updatedCase.status_policy.current_status } else { "failed" }
    if ($currentStatus -eq "failed") {
        $hasFailure = $true
    }

    $results += [pscustomobject]@{
        slug = $updatedCase.slug
        entry = $updatedCase.entry
        template = $updatedCase.template
        validation_mode = $updatedCase.validation_mode
        status = $currentStatus
        note = if ($null -ne $updatedCase.status_policy -and $updatedCase.status_policy.PSObject.Properties.Name -contains "last_note") { [string]$updatedCase.status_policy.last_note } else { "" }
    }
}

$summary = [pscustomobject]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString("o")
    failed = ($results | Where-Object { $_.status -eq "failed" }).Count
    blocked_external = ($results | Where-Object { $_.status -eq "blocked_external" }).Count
    smoke_passed = ($results | Where-Object { $_.status -eq "smoke_passed" }).Count
    passed = ($results | Where-Object { $_.status -eq "passed" }).Count
    results = $results
}

Set-Content -Path $summaryPath -Value (($summary | ConvertTo-Json -Depth 12) + "`n") -Encoding UTF8

if ($hasFailure) {
    exit 1
}

exit 0
