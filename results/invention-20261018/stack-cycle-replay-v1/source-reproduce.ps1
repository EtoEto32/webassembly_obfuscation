param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $repoRoot
if (Test-Path -LiteralPath $OutputDirectory) { throw 'OutputDirectory must be new.' }
python research/stack-cycle/experiment.py $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Build or recovery failed.' }
python research/stack-cycle/finish.py $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Correctness, interpreter, or performance failed.' }
python research/stack-cycle/edges.py $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Supplemental profile checks failed.' }
python research/stack-cycle/audit.py $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Audit failed.' }
