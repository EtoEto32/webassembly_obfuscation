[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
& docker run --rm --network none --cpus 2 --memory 2g --pids-limit 256 --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:rw,nosuid,nodev,size=512m --tmpfs /home/experiment:rw,nosuid,nodev,size=64m,uid=10001,gid=10001,mode=0700 --shm-size 256m wasm-hash-reference:local
if ($LASTEXITCODE -ne 0) {throw 'Offline browser isolation verification failed.'}
