[CmdletBinding()]
param(
    [string]$Version,
    [string]$OutputDirectory = "dist"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $repoRoot "plugins\baidu-netdisk\.codex-plugin\plugin.json"
$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = $manifest.version
}

if ($Version -notmatch '^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$') {
    throw "Version '$Version' is not a supported semantic version."
}

if ($manifest.version -ne $Version) {
    throw "Package version '$Version' does not match plugin manifest version '$($manifest.version)'."
}

$outputRoot = if ([System.IO.Path]::IsPathRooted($OutputDirectory)) {
    [System.IO.Path]::GetFullPath($OutputDirectory)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
}

New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

$packageName = "baidu-netdisk-codex-plugin-v$Version"
$zipPath = Join-Path $outputRoot "$packageName.zip"
$checksumPath = "$zipPath.sha256"
$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$tempRoot = Join-Path $tempBase ("baidu-netdisk-package-" + [guid]::NewGuid().ToString("N"))
$stagingRoot = Join-Path $tempRoot $packageName

try {
    New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null

    foreach ($file in @("README.md", "SECURITY.md", "CHANGELOG.md", "LICENSE")) {
        Copy-Item -LiteralPath (Join-Path $repoRoot $file) -Destination $stagingRoot
    }

    $marketplaceTarget = Join-Path $stagingRoot ".agents\plugins"
    New-Item -ItemType Directory -Force -Path $marketplaceTarget | Out-Null
    Copy-Item -LiteralPath (Join-Path $repoRoot ".agents\plugins\marketplace.json") -Destination $marketplaceTarget

    $pluginSource = Join-Path $repoRoot "plugins\baidu-netdisk"
    $pluginTarget = Join-Path $stagingRoot "plugins\baidu-netdisk"
    New-Item -ItemType Directory -Force -Path (Join-Path $pluginTarget ".codex-plugin") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $pluginTarget "scripts") | Out-Null

    Copy-Item -LiteralPath (Join-Path $pluginSource ".codex-plugin\plugin.json") -Destination (Join-Path $pluginTarget ".codex-plugin")
    Copy-Item -LiteralPath (Join-Path $pluginSource ".mcp.json") -Destination $pluginTarget
    Copy-Item -LiteralPath (Join-Path $pluginSource "README.md") -Destination $pluginTarget
    Get-ChildItem -LiteralPath (Join-Path $pluginSource "scripts") -File |
        Where-Object { $_.Extension -in @(".py", ".cmd") } |
        Copy-Item -Destination (Join-Path $pluginTarget "scripts")

    Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $checksumPath -Force -ErrorAction SilentlyContinue
    Compress-Archive -LiteralPath $stagingRoot -DestinationPath $zipPath -CompressionLevel Optimal

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    try {
        $entries = @($archive.Entries | ForEach-Object { $_.FullName.Replace("\", "/") })
        $requiredSuffixes = @(
            "/.agents/plugins/marketplace.json",
            "/plugins/baidu-netdisk/.codex-plugin/plugin.json",
            "/plugins/baidu-netdisk/.mcp.json",
            "/plugins/baidu-netdisk/scripts/server.py",
            "/plugins/baidu-netdisk/scripts/run_server.cmd"
        )
        foreach ($suffix in $requiredSuffixes) {
            if (-not ($entries | Where-Object { $_.EndsWith($suffix, [System.StringComparison]::Ordinal) })) {
                throw "Release package is missing required entry: $suffix"
            }
        }
        $forbidden = @($entries | Where-Object {
            $_ -match '(^|/)(__pycache__|credentials\.json|\.env)(/|$)' -or $_ -match '\.part$'
        })
        if ($forbidden.Count -gt 0) {
            throw "Release package contains forbidden entries: $($forbidden -join ', ')"
        }
    } finally {
        $archive.Dispose()
    }

    $hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath $checksumPath -Value "$hash  $([System.IO.Path]::GetFileName($zipPath))" -Encoding ascii

    Write-Output "Package: $zipPath"
    Write-Output "SHA-256: $checksumPath"
} finally {
    $resolvedTempRoot = [System.IO.Path]::GetFullPath($tempRoot)
    if ($resolvedTempRoot.StartsWith($tempBase, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolvedTempRoot).StartsWith("baidu-netdisk-package-", [System.StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $resolvedTempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
