param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $repoRoot
if (Test-Path -LiteralPath $OutputDirectory) { throw 'OutputDirectory must be new.' }
python research/rounding-region/experiment.py $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
node research/rounding-region/check.cjs $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Differential execution failed.' }
foreach ($action in @('interpreter','controls','timing','summarize')) {
    python research/rounding-region/finish.py $action $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw "$action failed." }
}
python research/rounding-region/adaptive_cost.py $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Adaptive analysis failed.' }
