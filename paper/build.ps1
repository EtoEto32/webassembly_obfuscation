# Run with: powershell -File .\paper\build.ps1
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'

foreach ($taskCommand in @('platex', 'pbibtex', 'dvipdfmx')) {
    if (-not (Get-Command $taskCommand -ErrorAction SilentlyContinue)) {
        throw "Required command '$taskCommand' was not found. See paper/README.md for local and Overleaf build instructions."
    }
}

Push-Location -LiteralPath $PSScriptRoot
try {
    & platex '-kanji=utf8' '-interaction=nonstopmode' '-halt-on-error' '-file-line-error' 'main.tex'
    if ($LASTEXITCODE -ne 0) { throw 'First pLaTeX pass failed.' }
    & pbibtex '-kanji=utf8' 'main'
    if ($LASTEXITCODE -ne 0) { throw 'pBibTeX failed.' }
    & platex '-kanji=utf8' '-interaction=nonstopmode' '-halt-on-error' '-file-line-error' 'main.tex'
    if ($LASTEXITCODE -ne 0) { throw 'Second pLaTeX pass failed.' }
    & platex '-kanji=utf8' '-interaction=nonstopmode' '-halt-on-error' '-file-line-error' 'main.tex'
    if ($LASTEXITCODE -ne 0) { throw 'Third pLaTeX pass failed.' }
    & dvipdfmx '-o' 'main.pdf' 'main.dvi'
    if ($LASTEXITCODE -ne 0) { throw 'dvipdfmx failed.' }
    Write-Output (Join-Path $PSScriptRoot 'main.pdf')
}
finally {
    Pop-Location
}
