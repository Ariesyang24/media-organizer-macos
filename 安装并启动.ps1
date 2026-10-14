param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Launcher = Join-Path $ProjectRoot 'launch_media_organizer_safe_drag_v53.pyw'
$Requirements = Join-Path $ProjectRoot 'requirements-windows.txt'

function Show-Step([string]$Message) {
    Write-Host "`n▶ $Message" -ForegroundColor Cyan
}

function Find-Python {
    $candidates = @(
        @{ File = 'py'; Args = @('-3.12') },
        @{ File = 'py'; Args = @('-3.11') },
        @{ File = 'python'; Args = @() }
    )
    foreach ($candidate in $candidates) {
        try {
            & $candidate.File @($candidate.Args) -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        } catch {}
    }
    return $null
}

Write-Host 'Media Organizer 一键安装与启动' -ForegroundColor White
Write-Host '程序会自动检查 Python、安装依赖并创建快捷方式。'

$Python = Find-Python
if ($CheckOnly) {
    if (-not (Test-Path -LiteralPath $Launcher)) { throw '找不到正式启动程序。' }
    if (-not (Test-Path -LiteralPath $Requirements)) { throw '找不到运行组件清单。' }
    Write-Host ('自检通过：启动程序、依赖清单和安装流程完整；Python=' + [bool]$Python) -ForegroundColor Green
    exit 0
}
if (-not $Python) {
    Show-Step '正在安装 Python 3.12（只需执行一次）'
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host '当前 Windows 没有可用的自动安装工具。' -ForegroundColor Yellow
        Write-Host '即将打开 Python 官方下载页面；安装时请勾选“Add Python to PATH”，完成后再次双击本文件。'
        Start-Process 'https://www.python.org/downloads/windows/'
        exit 1
    }
    & winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'Python 自动安装失败，请检查网络后重试。' }
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
    $Python = Find-Python
    if (-not $Python) {
        Write-Host 'Python 已安装。请关闭本窗口，再双击“一键安装并启动.cmd”。' -ForegroundColor Yellow
        exit 1
    }
}

Show-Step '正在安装程序运行组件'
& $Python.File @($Python.Args) -m pip install --disable-pip-version-check --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip 更新失败。' }
& $Python.File @($Python.Args) -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) { throw '运行组件安装失败，请检查网络后重试。' }

Show-Step '正在创建桌面和开始菜单快捷方式'
$PythonExe = (& $Python.File @($Python.Args) -c 'import sys; print(sys.executable)').Trim()
$PythonwExe = Join-Path (Split-Path -Parent $PythonExe) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $PythonwExe)) { $PythonwExe = $PythonExe }
$Shell = New-Object -ComObject WScript.Shell
$ShortcutLocations = @(
    (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Media Organizer.lnk'),
    (Join-Path ([Environment]::GetFolderPath('Programs')) 'Media Organizer.lnk')
)
foreach ($ShortcutPath in $ShortcutLocations) {
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $PythonwExe
    $Shortcut.Arguments = '"' + $Launcher + '"'
    $Shortcut.WorkingDirectory = $ProjectRoot
    $Shortcut.Description = 'Media Organizer 素材整理工具'
    $Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,127"
    $Shortcut.Save()
}

Show-Step '安装完成，正在启动 Media Organizer'
Start-Process -FilePath $PythonwExe -ArgumentList @('"' + $Launcher + '"') -WorkingDirectory $ProjectRoot
Start-Sleep -Seconds 2
Write-Host '以后直接双击桌面的“Media Organizer”即可。' -ForegroundColor Green
