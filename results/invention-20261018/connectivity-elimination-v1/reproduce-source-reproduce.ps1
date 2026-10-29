param([string]$OutputDirectory = 'results/invention-20261018/connectivity-elimination-replay-v1')
$ErrorActionPreference = 'Stop'
$ResearchRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
function Invoke-CheckedPython {
    param([string[]]$Arguments)
    & python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python stage failed: $($Arguments[0])" }
}
Push-Location $ResearchRoot
try {
    if (Test-Path -LiteralPath $OutputDirectory) { throw 'Output directory already exists; choose a fresh path.' }
    Invoke-CheckedPython @('research/connectivity-elimination/build.py', $OutputDirectory)
    Invoke-CheckedPython @('research/connectivity-elimination/finish.py', 'prepare', $OutputDirectory)
    & node research/connectivity-elimination/verify.cjs $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'V8 correctness stage failed' }
    Invoke-CheckedPython @('research/connectivity-elimination/edge_cases.py', $OutputDirectory)
    Invoke-CheckedPython @('research/connectivity-elimination/finish.py', 'interpreter', $OutputDirectory)
    Invoke-CheckedPython @('research/connectivity-elimination/finish.py', 'timing', $OutputDirectory)
    Invoke-CheckedPython @('research/connectivity-elimination/analysis_timing.py', $OutputDirectory)
    Invoke-CheckedPython @('research/connectivity-elimination/summarize.py', $OutputDirectory)
}
finally { Pop-Location }
