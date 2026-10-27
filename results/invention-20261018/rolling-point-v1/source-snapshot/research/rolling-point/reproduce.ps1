param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$PythonCommand = 'python'
)
$ErrorActionPreference = 'Stop'
$taskRepo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $taskRepo
try {
    if (Test-Path -LiteralPath $OutputDirectory) { throw 'Use a new output directory.' }
    & $PythonCommand research/rolling-point/build.py $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'build failed' }
    & node research/rolling-point/check.cjs $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'check failed' }
    & $PythonCommand research/rolling-point/attack.py $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'attack failed' }
    foreach ($taskPart in @('engines', 'domain', 'performance')) {
        & $PythonCommand research/rolling-point/followup.py $OutputDirectory --part $taskPart
        if ($LASTEXITCODE -ne 0) { throw "$taskPart failed" }
    }
    & $PythonCommand research/rolling-point/edges.py $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'edges failed' }
    & $PythonCommand research/rolling-point/report.py $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'report failed' }
    & $PythonCommand research/rolling-point/record.py $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw 'record failed' }
}
finally { Pop-Location }
