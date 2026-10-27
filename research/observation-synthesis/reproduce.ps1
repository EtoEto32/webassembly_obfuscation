param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$PythonCommand = 'python',
    [string]$NodeCommand = 'node'
)
$ErrorActionPreference = 'Stop'
$repositoryDirectory = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $repositoryDirectory
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Output directory must not exist.' }
function Invoke-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Program" }
}
$scriptDirectory = 'research/observation-synthesis'
Invoke-Checked $PythonCommand @("$scriptDirectory/suite.py", $OutputDirectory)
& $NodeCommand --no-liftoff --no-wasm-tier-up --no-wasm-lazy-compilation --trace-wasm-compilation-times "$scriptDirectory/suite_runtime.cjs" $OutputDirectory run > (Join-Path $OutputDirectory 'runtime.log')
if ($LASTEXITCODE -ne 0) { throw 'Runtime checks failed; inspect runtime.log.' }
# Normalize PowerShell redirection encoding to UTF-8 for the Python log checker.
$runtimeLogPath = Join-Path $OutputDirectory 'runtime.log'
$runtimeLogText = Get-Content -LiteralPath $runtimeLogPath -Raw
[System.IO.File]::WriteAllText((Resolve-Path $runtimeLogPath).Path, $runtimeLogText, (New-Object System.Text.UTF8Encoding($false)))
Invoke-Checked $NodeCommand @("$scriptDirectory/suite_runtime.cjs", $OutputDirectory, 'attack')
Invoke-Checked $NodeCommand @("$scriptDirectory/suite_runtime.cjs", $OutputDirectory, 'memory')
Invoke-Checked $PythonCommand @("$scriptDirectory/verify_suite.py", $OutputDirectory)
Invoke-Checked $PythonCommand @("$scriptDirectory/supplement.py", $OutputDirectory, 'cross')
Invoke-Checked $PythonCommand @("$scriptDirectory/supplement.py", $OutputDirectory, 'resources', '--label', 'transform-resources-sequential')
Invoke-Checked $PythonCommand @("$scriptDirectory/ablation.py", $OutputDirectory)
Invoke-Checked $PythonCommand @("$scriptDirectory/summarize_suite.py", $OutputDirectory)
Write-Output "Completed checks and tables: $OutputDirectory"
