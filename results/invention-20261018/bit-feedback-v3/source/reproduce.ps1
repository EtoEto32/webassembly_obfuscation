param([string]$Output = 'results/invention-20261018/bit-feedback-reproduction')
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location -LiteralPath $taskRoot
try {
    python research/bit-feedback/experiment.py $Output
    if ($LASTEXITCODE -ne 0) { throw 'Experiment failed' }
    python research/bit-feedback/measure.py $Output
    if ($LASTEXITCODE -ne 0) { throw 'Measurement failed' }
    python research/bit-feedback/edges.py $Output
    if ($LASTEXITCODE -ne 0) { throw 'Controls failed' }
    python research/bit-feedback/audit.py $Output
    if ($LASTEXITCODE -ne 0) { throw 'Audit failed' }
} finally { Pop-Location }
