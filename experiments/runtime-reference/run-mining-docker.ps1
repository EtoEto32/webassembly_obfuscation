[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PoolConfig,
    [Parameter(Mandatory=$true)][string]$ModuleSha256,
    [Parameter(Mandatory=$true)][ValidateRange(1,256)][int]$Threads,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$')][string]$RunId,
    [switch]$Execute
)
$ErrorActionPreference = 'Stop'
if ($ModuleSha256 -notmatch '^[a-f0-9]{64}$') { throw 'Invalid module SHA-256' }
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskConfig = (Resolve-Path -LiteralPath $PoolConfig).Path
$taskConfigData = Get-Content -LiteralPath $taskConfig -Raw | ConvertFrom-Json
if ($Execute -and ($taskConfigData.operator_verified -ne $true -or $taskConfigData.user_owned_identifier -ne $true -or [string]::IsNullOrWhiteSpace($taskConfigData.address))) {
    throw 'Execution requires verified operator conditions and the user-owned public identifier'
}
$taskOutputRoot = Join-Path $taskRoot 'results/runtime-mining/runs'
if (-not (Test-Path -LiteralPath $taskOutputRoot)) { New-Item -ItemType Directory -Path $taskOutputRoot | Out-Null }
if (Test-Path -LiteralPath (Join-Path $taskOutputRoot $RunId)) { throw 'Run directory already exists; choose a new RunId' }
$taskNetwork = 'none'
if ($Execute) { $taskNetwork = 'bridge' }
$taskImageId = (& docker image inspect wasm-hash-reference:local --format '{{.Id}}').Trim()
if ($LASTEXITCODE -ne 0 -or $taskImageId -notmatch '^sha256:[a-f0-9]{64}$') { throw 'Cannot identify runtime image' }
$taskArguments = @('run','--rm','--network',$taskNetwork,'--cpus','2','--memory','2g','--pids-limit','256',
    '--env',"EXPERIMENT_IMAGE_ID=$taskImageId",
    '--cap-drop','ALL','--security-opt','no-new-privileges','--read-only',
    '--tmpfs','/tmp:rw,nosuid,nodev,size=512m',
    '--tmpfs','/home/experiment:rw,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=0700',
    '--shm-size','256m')
$taskMounts = @(
    @($PSScriptRoot,'/work/experiments/runtime-reference','readonly'),
    @($taskConfig,'/inputs/pool.json','readonly'),
    @((Join-Path $taskRoot "data/objects/$ModuleSha256.bin"),"/work/data/objects/$ModuleSha256.bin",'readonly'),
    @((Join-Path $taskRoot 'results/mining-methods/input-manifest.csv'),'/work/results/mining-methods/input-manifest.csv','readonly'),
    @((Join-Path $taskRoot 'results/runtime-mining/algorithm-contracts.json'),'/work/results/runtime-mining/algorithm-contracts.json','readonly'),
    @((Join-Path $taskRoot 'results/runtime-mining/proxy-provenance.json'),'/work/results/runtime-mining/proxy-provenance.json','readonly'),
    @((Join-Path $taskRoot '.tools/xmrig-proxy-6.18.0/xmrig-proxy-6.18.0/xmrig-proxy'),'/work/.tools/xmrig-proxy-6.18.0/xmrig-proxy-6.18.0/xmrig-proxy','readonly'),
    @($taskOutputRoot,'/work/results/runtime-mining/runs','')
)
foreach ($taskMount in $taskMounts) {
    $taskSource = (Resolve-Path -LiteralPath $taskMount[0]).Path
    $taskSpecification = "type=bind,source=$taskSource,target=$($taskMount[1])"
    if ($taskMount[2]) { $taskSpecification += ',readonly' }
    $taskArguments += @('--mount',$taskSpecification)
}
$taskArguments += @('--workdir','/work','--entrypoint','python3',$taskImageId,
    '-P','/work/experiments/runtime-reference/run_mining.py','--pool-config','/inputs/pool.json',
    '--sha256',$ModuleSha256,'--threads',"$Threads",'--output',"/work/results/runtime-mining/runs/$RunId")
if (-not $Execute) { $taskArguments += '--validate-only' }
& docker @taskArguments
if ($LASTEXITCODE -ne 0) { throw 'Container validation or measurement failed; do not interpret this as successful mining' }
