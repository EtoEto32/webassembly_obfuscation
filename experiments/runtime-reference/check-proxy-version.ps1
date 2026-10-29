$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskToolRoot = Join-Path $taskRoot '.tools/xmrig-proxy-6.18.0'
$taskArchive = Join-Path $taskToolRoot 'xmrig-proxy-6.18.0-linux-static-x64.tar.gz'
$taskExpected = 'fe83dc89466fbd828a1cd71145021a3908950ac2bb8b3a9af9f6d8bf05352ea3'
if ((Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskExpected) { throw 'Archive checksum mismatch' }
$taskProxy = Join-Path $taskToolRoot 'xmrig-proxy-6.18.0/xmrig-proxy'
$taskOriginal = Join-Path $taskRoot 'data/upstream/wasm_evasion/malware_reproduction/rq3/replace_experiments/xmrig-proxy'
$taskOriginalText = [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($taskOriginal))
if (-not $taskOriginalText.Contains('xmrig-proxy 6.18.0')) { throw 'Original proxy version was not confirmed' }
$taskOutput = & docker run --rm --network none --cap-drop ALL --security-opt no-new-privileges --read-only --mount "type=bind,source=$taskProxy,target=/opt/xmrig-proxy,readonly" --entrypoint /opt/xmrig-proxy wasm-hash-reference:local --version 2>&1
if ($LASTEXITCODE -ne 0) { throw "Proxy version check failed: $taskOutput" }
if (($taskOutput -join "`n") -notmatch '6\.18\.0') { throw 'Unexpected runtime version' }
$taskOutput | Set-Content -Encoding utf8 (Join-Path $taskRoot 'results/runtime-mining/proxy-version.log')
$taskImage = (& docker image inspect wasm-hash-reference:local --format '{{.Id}}').Trim()
if ($LASTEXITCODE -ne 0) { throw 'Image identity check failed' }
[ordered]@{
  utc = [DateTime]::UtcNow.ToString('o')
  version = '6.18.0'
  official_archive_url = 'https://github.com/xmrig/xmrig-proxy/releases/download/v6.18.0/xmrig-proxy-6.18.0-linux-static-x64.tar.gz'
  official_checksums_url = 'https://github.com/xmrig/xmrig-proxy/releases/download/v6.18.0/SHA256SUMS'
  archive_sha256 = $taskExpected
  binary_sha256 = (Get-FileHash -LiteralPath $taskProxy -Algorithm SHA256).Hash.ToLowerInvariant()
  original_binary_sha256 = (Get-FileHash -LiteralPath $taskOriginal -Algorithm SHA256).Hash.ToLowerInvariant()
  original_platform = 'macOS x86_64'
  runtime_platform = 'Linux x86_64; musl loader'
  docker_image_id = $taskImage
  external_connection = $false
  mining_executed = $false
} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $taskRoot 'results/runtime-mining/proxy-provenance.json')
$taskOutput
