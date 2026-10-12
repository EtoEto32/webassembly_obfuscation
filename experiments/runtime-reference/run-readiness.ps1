[CmdletBinding()]
param(
    [string]$ModuleSha256 = '83bf23cabddce772c1e2cf38a020c067077475d6231d34a36260b5b2fb3882f2'
)
$ErrorActionPreference = 'Stop'
if ($ModuleSha256 -notmatch '^[a-f0-9]{64}$') { throw 'Invalid module digest' }
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskModule = Join-Path $taskRoot "data/objects/$ModuleSha256.bin"
$taskGlue = Join-Path $PSScriptRoot 'hash-adapter.js'
$taskScript = Join-Path $PSScriptRoot 'readiness.py'
if ((Get-FileHash -LiteralPath $taskModule -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ModuleSha256) { throw 'Module digest mismatch' }
& docker run --rm --network none --cpus 2 --memory 2g --pids-limit 256 --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,nosuid,nodev,size=512m --tmpfs /home/experiment:rw,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=0700 --shm-size 256m --mount "type=bind,source=$taskModule,target=/inputs/module.wasm,readonly" --mount "type=bind,source=$taskGlue,target=/inputs/hash-adapter.js,readonly" --mount "type=bind,source=$taskScript,target=/opt/experiment/readiness.py,readonly" --entrypoint python3 wasm-hash-reference:local /opt/experiment/readiness.py
if ($LASTEXITCODE -ne 0) { throw 'Offline Wasm readiness check failed' }
