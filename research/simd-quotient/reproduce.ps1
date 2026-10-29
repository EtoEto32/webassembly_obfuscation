param([string]$Output='results/invention-20261018/simd-quotient-reproduction',[string]$Compare='')
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location -LiteralPath $taskRoot
try {
    python research/simd-quotient/run.py $Output
    if ($LASTEXITCODE -ne 0) { throw 'SIMD experiment failed' }
    if ($Compare) { python research/simd-quotient/finish.py $Output --compare $Compare }
    else { python research/simd-quotient/finish.py $Output }
    if ($LASTEXITCODE -ne 0) { throw 'SIMD audit failed' }
} finally { Pop-Location }
