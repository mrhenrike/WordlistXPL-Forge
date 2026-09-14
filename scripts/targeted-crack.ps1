#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Build a targeted wordlist plus a composite-affix rule set and crack with the
  rules integrated directly into the hashcat flow.

.DESCRIPTION
  One consolidated pipeline:
    1. combiner  -> compact base wordlist (per-component CamelCase + linguistic
                    linking-word connectors)
    2. affix     -> composite-affix hashcat rule set (core, special+core,
                    core+special, special+core+special)
    3. hashcat   -> applies the rule set on the GPU during cracking (-r), so the
                    huge expansion never has to be written to disk.

  Use -Expand to also materialize the fully expanded wordlist. Use -Run with
  -HashFile and -HashMode to launch hashcat; otherwise the ready command is
  printed.

.EXAMPLE
  ./scripts/targeted-crack.ps1 -Keywords alpha,bravo,charlie -Dates '0724,1988'

.EXAMPLE
  ./scripts/targeted-crack.ps1 -Keywords alpha,bravo -Dates '0724' `
    -HashFile hashes.txt -HashMode 1000 -Run
#>
param(
    [Parameter(Mandatory = $true)][string[]]$Keywords,
    [Parameter(Mandatory = $true)][string]$Dates,
    [string]$Specials = '!,@,#',
    [string]$LinkLang = 'pt',
    [string]$Connectors = 'EMPTY,_,.,na,no,da',
    [string]$OutDir = 'generated',
    [string]$HashFile,
    [string]$HashMode,
    [switch]$Expand,
    [switch]$Run
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$wlf = Join-Path $root 'wlf.py'
if (-not (Test-Path $wlf)) { throw "wlf.py not found at $wlf" }

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$bases = Join-Path $OutDir 'targeted_bases.lst'
$rule = Join-Path $OutDir 'targeted_affix.rule'

Write-Host "[1/3] combiner -> $bases"
python $wlf combiner $Keywords --titlecase --link-lang $LinkLang --assume-yes --connectors $Connectors -o $bases
if ($LASTEXITCODE -ne 0) { throw "combiner failed" }

Write-Host "[2/3] affix rule set -> $rule"
python $wlf affix $bases --dates $Dates --specials $Specials --emit-ruleset $rule
if ($LASTEXITCODE -ne 0) { throw "affix ruleset failed" }

if ($Expand) {
    $expanded = Join-Path $OutDir 'targeted_expanded.lst'
    Write-Host "[2b] affix expanded wordlist -> $expanded"
    python $wlf affix $bases --dates $Dates --specials $Specials -o $expanded
    if ($LASTEXITCODE -ne 0) { throw "affix expand failed" }
}

if ($HashFile -and $HashMode) {
    $hc = "hashcat -a 0 -m $HashMode `"$HashFile`" `"$bases`" -r `"$rule`""
}
else {
    $hc = "hashcat -a 0 -m <MODE> <HASHFILE> `"$bases`" -r `"$rule`""
}
Write-Host "[3/3] cracking command (rules integrated):"
Write-Host "  $hc"

if ($Run) {
    if (-not (Get-Command hashcat -ErrorAction SilentlyContinue)) {
        Write-Warning "hashcat not found in PATH; skipping run."
        return
    }
    if (-not ($HashFile -and $HashMode)) {
        Write-Warning "provide -HashFile and -HashMode to run hashcat."
        return
    }
    & hashcat -a 0 -m $HashMode $HashFile $bases -r $rule
}
