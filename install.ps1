# cc-ra Skill installer (PowerShell 7)
#
# cc-ra/skill/ 의 내용을 .claude/skills/cc-ra/ 로 복사해 Claude Code 가
# /cc-ra 슬래시 커맨드로 인식하게 만든다.
# lib/ 도 skill/ 하위에 있으므로 함께 복사됨 → 설치 후 자급자족 구조.
#
# 사용:
#   D:\Tools\PS7\7\pwsh.exe -NoProfile -ExecutionPolicy Bypass -File install.ps1
# 또는 Git Bash:
#   "D:/Tools/PS7/7/pwsh.exe" -NoProfile -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"
$Repo   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $Repo "skill"
$Target = Join-Path $env:USERPROFILE ".claude/skills/cc-ra"

Write-Host "[cc-ra install]"
Write-Host "  source : $Source"
Write-Host "  target : $Target"

if (-not (Test-Path $Source)) {
    Write-Error "source not found: $Source"
}

if (-not (Test-Path $Target)) {
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
}

# 기존 내용 정리 후 복사 (symlink 회피 — Windows 권한 안전)
Get-ChildItem -Path $Target -Recurse -Force |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $Source "*") -Destination $Target -Recurse -Force

Write-Host ""
Write-Host "[cc-ra install] OK"
Write-Host ""
Write-Host "다음 단계:"
Write-Host "  1) Python 의존성 설치 (한 번):"
Write-Host "       pip install -r `"$Target\requirements.txt`""
Write-Host "  2) (권장) cargo-modules:"
Write-Host "       cargo install cargo-modules"
Write-Host "  3) Claude Code 재시작 후 /cc-ra 사용 가능"
Write-Host ""
Write-Host "  Python 헬퍼 위치: $Target\lib"
