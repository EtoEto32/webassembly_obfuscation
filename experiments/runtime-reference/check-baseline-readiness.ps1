[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskManifest = Import-Csv (Join-Path $taskRoot 'results/mining-methods/input-manifest.csv')
$taskInputs = $taskManifest | Where-Object { $_.method -eq 'unobfuscated' }
if (@($taskInputs).Count -ne 20) { throw 'Expected the manifest-defined 20 normal inputs' }
$taskDirectory = Join-Path $taskRoot ('results/runtime-mining/baseline-readiness-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $taskDirectory | Out-Null
$taskResults = @()
foreach ($taskInput in $taskInputs) {
    $taskLog = Join-Path $taskDirectory ($taskInput.sha256 + '.log')
    $taskStatus = 'failed'
    try {
        & (Join-Path $PSScriptRoot 'run-readiness.ps1') -ModuleSha256 $taskInput.sha256 *>&1 | Tee-Object -FilePath $taskLog
        $taskStatus = 'initialization-ready'
    } catch {
        $_ | Out-String | Add-Content -LiteralPath $taskLog
    }
    $taskResults += [pscustomobject]@{
        program = $taskInput.program
        release = $taskInput.release
        sha256 = $taskInput.sha256
        status = $taskStatus
        hashes_measured = $false
        pool_connected = $false
        log = $taskLog
    }
    $taskResults | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $taskDirectory 'summary.json') -Encoding UTF8
    Write-Output ("READINESS {0} {1}: {2}" -f $taskInput.program, $taskInput.release, $taskStatus)
}
