$ErrorActionPreference = 'Stop'
$researchRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$researchItem = Get-Content -LiteralPath (Join-Path $researchRoot 'experiments/archive-registry.json') -Raw | ConvertFrom-Json | Where-Object { $_.id -eq 'proof-of-theft' }
$researchUrl = 'https://drops.dagstuhl.de/storage/artifacts/darts-vol012/darts-vol012-issue001_ecoop2026/25184/DARTS-12-1-19-artifact-ac935f9f40e42fd90160d07151b61ffe.zip'
$researchDest = Join-Path $researchRoot 'data/archives/proof-of-theft.zip'
$researchPartial = $researchDest + '.partial'
if (!(Test-Path -LiteralPath $researchDest)) {
    Write-Output 'Downloading official DROPS artifact mirror with Windows certificate validation'
    Invoke-WebRequest -Uri $researchUrl -OutFile $researchPartial -Resume
    if ((Get-Item -LiteralPath $researchPartial).Length -ne $researchItem.bytes) { throw 'Archive size mismatch' }
    if ((Get-FileHash -LiteralPath $researchPartial -Algorithm MD5).Hash.ToLowerInvariant() -ne $researchItem.md5) { throw 'Publisher MD5 mismatch' }
    Move-Item -LiteralPath $researchPartial -Destination $researchDest
}
$researchReceipt = [ordered]@{
    id = $researchItem.id
    dataset = $researchItem.dataset
    filename = $researchItem.filename
    url = $researchUrl
    alternate_url = $researchItem.url
    bytes = (Get-Item -LiteralPath $researchDest).Length
    sha256 = (Get-FileHash -LiteralPath $researchDest -Algorithm SHA256).Hash.ToLowerInvariant()
    md5 = (Get-FileHash -LiteralPath $researchDest -Algorithm MD5).Hash.ToLowerInvariant()
    retrieved_utc = [DateTime]::UtcNow.ToString('o')
}
if ($researchReceipt.md5 -ne $researchItem.md5) { throw 'Final artifact MD5 mismatch' }
$researchReceipt | ConvertTo-Json | Set-Content -LiteralPath ($researchDest + '.receipt.json') -Encoding utf8
$researchReceipt | ConvertTo-Json
