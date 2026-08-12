# src/modules/script_templates.py
# 所有脚本模板集中于此，方便独立修改

from config import UNLOCK_USB_PS1
from src.core.runtime_config import toolkit_cfg
from src.modules.service_manager import get_mmpc_cmd


def _mmcp_stop():
    return get_mmpc_cmd(True)


# ══════════════════════════════════════════════════════════
# 内联 PowerShell 片段（避免外部 ps1 文件依赖）
# ══════════════════════════════════════════════════════════

KB_PS_INLINE = (
    "$target = 'KbFilter';"
    "$guids = @('{4D36E96B-E325-11CE-BFC1-08002BE10318}','{4D36E96F-E325-11CE-BFC1-08002BE10318}','{745a17a0-74d3-11d0-b6fe-00a0c90f57da}');"
    "foreach ($g in $guids) {"
    "  $p = 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\' + $g;"
    "  foreach ($n in @('UpperFilters','LowerFilters')) {"
    "    $v = Get-ItemProperty -Path $p -Name $n -ErrorAction SilentlyContinue;"
    "    if ($v -and $v.$n -contains $target) {"
    "      $new = $v.$n | Where-Object { $_ -ne $target };"
    "      if ($new) { Set-ItemProperty -Path $p -Name $n -Value $new; Write-Host ('[OK] '+$g+' '+$n+': removed '+$target) }"
    "      else { Remove-ItemProperty -Path $p -Name $n -ErrorAction SilentlyContinue; Write-Host ('[OK] '+$g+' '+$n+': removed '+$target+' (empty)') }"
    "    }"
    "  }"
    "};"
    "Get-PnpDevice -Class Keyboard -ErrorAction SilentlyContinue | ForEach-Object { Disable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue; Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue };"
    "Get-PnpDevice -Class Mouse -ErrorAction SilentlyContinue | ForEach-Object { Disable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue; Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue };"
    "Write-Host 'Done.'"
)

USB_PS_INLINE = (
    "$target = 'easyusbflt';"
    "$guids = @('{36FC9E60-C465-11CF-8056-444553540000}','{745a17a0-74d3-11d0-b6fe-00a0c90f57da}');"
    "foreach ($g in $guids) {"
    "  $p = 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\' + $g;"
    "  foreach ($n in @('UpperFilters','LowerFilters')) {"
    "    $v = Get-ItemProperty -Path $p -Name $n -ErrorAction SilentlyContinue;"
    "    if ($v -and $v.$n -contains $target) {"
    "      $new = $v.$n | Where-Object { $_ -ne $target };"
    "      if ($new) { Set-ItemProperty -Path $p -Name $n -Value $new; Write-Host ('[OK] '+$g+' '+$n+': removed '+$target) }"
    "      else { Remove-ItemProperty -Path $p -Name $n -ErrorAction SilentlyContinue; Write-Host ('[OK] '+$g+' '+$n+': removed '+$target+' (empty)') }"
    "    }"
    "  }"
    "};"
    "Get-PnpDevice -Class HIDClass -ErrorAction SilentlyContinue | ForEach-Object { Disable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue; Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue };"
    "Get-PnpDevice -Class USB -ErrorAction SilentlyContinue | ForEach-Object { Disable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue; Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue };"
)


# ══════════════════════════════════════════════════════════
# 脚本模板
# ══════════════════════════════════════════════════════════

def tpl_unlock_network() -> str:
    return f"""@ECHO OFF
title Unlock-Network

{_mmcp_stop()}
:a
taskkill /f /t /im {toolkit_cfg.student_exe_name}
taskkill /f /t /im DeviceControl_x64.exe
goto a
"""


def tpl_unlock_usb_ps1() -> str:
    return f"""$target = 'easyusbflt'
$guids = @('{{36FC9E60-C465-11CF-8056-444553540000}}','{{745a17a0-74d3-11d0-b6fe-00a0c90f57da}}')
foreach ($guid in $guids) {{
    $path = 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\' + $guid
    foreach ($name in @('UpperFilters','LowerFilters')) {{
        $v = Get-ItemProperty -Path $path -Name $name -ErrorAction SilentlyContinue
        if ($v -and $v.$name -contains $target) {{
            $new = $v.$name | Where-Object {{ $_ -ne $target }}
            if ($new) {{
                Set-ItemProperty -Path $path -Name $name -Value $new
                Write-Host ('[OK] ' + $guid + ' ' + $name + ': removed ' + $target + ', left: ' + ($new -join ','))
            }} else {{
                Remove-ItemProperty -Path $path -Name $name -ErrorAction SilentlyContinue
                Write-Host ('[OK] ' + $guid + ' ' + $name + ': removed ' + $target + ' (deleted empty value)')
            }}
        }}
    }}
}}
Get-PnpDevice -Class HIDClass -ErrorAction SilentlyContinue | ForEach-Object {{
    Disable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
    Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
}}
Get-PnpDevice -Class USB -ErrorAction SilentlyContinue | ForEach-Object {{
    Disable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
    Enable-PnpDevice -InstanceId $_.InstanceId -Confirm:$false -ErrorAction SilentlyContinue
}}
"""


def tpl_unlock_usb() -> str:
    return f"""@ECHO OFF
title Unlock-USB

{_mmcp_stop()}
taskkill /f /t /im {toolkit_cfg.student_exe_name}
taskkill /f /t /im DeviceControl_x64.exe

sc stop easyusbflt
sc delete easyusbflt

del /f /q "{toolkit_cfg.oseasy_path}easyusbflt.sys"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0{UNLOCK_USB_PS1}"

shutdown /l
"""


def tpl_unlock_keyboard() -> str:
    return f"""@ECHO OFF
title Unlock-Keyboard

{_mmcp_stop()}
taskkill /f /t /im {toolkit_cfg.student_exe_name}
taskkill /f /t /im BlackSlient.exe

sc stop KbFilter
sc stop ProcFireWall
sc delete KbFilter
sc delete ProcFireWall

del /f /q "{toolkit_cfg.oseasy_path}KbFilter.sys"
del /f /q "{toolkit_cfg.oseasy_path}ProcFireWall.sys"
del /f /q "{toolkit_cfg.oseasy_path}LockKeyboard.dll"
del /f /q "{toolkit_cfg.oseasy_path}LoadDriver.exe"
del /f /q "{toolkit_cfg.oseasy_path}KbDriver.exe"

powershell -NoProfile -ExecutionPolicy Bypass -Command {KB_PS_INLINE}

shutdown /l
"""


def tpl_unlock_all() -> str:
    return f"""@ECHO OFF
title Unlock-All

{_mmcp_stop()}

:: ── 杀进程 ──
taskkill /f /t /im {toolkit_cfg.student_exe_name}
taskkill /f /t /im BlackSlient.exe
taskkill /f /t /im DeviceControl_x64.exe
taskkill /f /t /im MultiClient.exe
taskkill /f /t /im ScreenRender.exe

:: ── 停驱动服务 ──
sc stop OeNetLimit
sc stop easyusbflt
sc stop KbFilter
sc stop ProcFireWall

:: ── 删驱动服务 ──
sc delete OeNetLimit
sc delete easyusbflt
sc delete KbFilter
sc delete ProcFireWall

:: ── 删驱动文件 ──
del /f /q "{toolkit_cfg.oseasy_path}OeNetLimit.sys"
del /f /q "{toolkit_cfg.oseasy_path}oenetlimitx64.cat"
del /f /q "{toolkit_cfg.oseasy_path}easyusbflt.sys"
del /f /q "{toolkit_cfg.oseasy_path}KbFilter.sys"
del /f /q "{toolkit_cfg.oseasy_path}ProcFireWall.sys"
del /f /q "{toolkit_cfg.oseasy_path}LockKeyboard.dll"
del /f /q "{toolkit_cfg.oseasy_path}LoadDriver.exe"
del /f /q "{toolkit_cfg.oseasy_path}KbDriver.exe"

:: ── 清理注册表 UpperFilters ──
powershell -NoProfile -ExecutionPolicy Bypass -Command {KB_PS_INLINE}
powershell -NoProfile -ExecutionPolicy Bypass -Command {USB_PS_INLINE}

:: ── 注销以刷新设备 ──
shutdown /l
"""


def tpl_process_killer_all() -> str:
    return (
        f"@ECHO OFF\n"
        f"title Process-Killer_All\n"
        f":awa\n"
        f"for %%p in (Ctsc_Multi.exe,DeviceControl_x64.exe,HRMon.exe,"
        f"MultiClient.exe,OActiveII-Client.exe,OEClient.exe,OELogSystem.exe,"
        f"OEUpdate.exe,OEProtect.exe,ProcessProtect.exe,RunClient.exe,"
        f"ServerOSS.exe,{toolkit_cfg.student_exe_name},wfilesvr.exe,"
        f"tvnserver.exe,updatefilesvr.exe,ScreenRender.exe) "
        f"do taskkill /f /IM %%p\n"
        f"goto awa\n"
    )


def tpl_process_killer_student() -> str:
    return f"""@ECHO OFF
title Process-Killer_Student

{_mmcp_stop()}

taskkill /f /t /im MultiClient.exe
taskkill /f /t /im BlackSlient.exe
:a
taskkill /f /t /im {toolkit_cfg.student_exe_name}
goto a
"""


def tpl_files_delete(delMtc: bool, shutdown: bool) -> str:
    lines = [
        f"@ECHO OFF",
        f"title Files-Delete",
        f"cd /D {toolkit_cfg.oseasy_path}",
        f"timeout 1",
        f"del /F /S LockKeyboard.dll",
        f"del /F /S LoadDriver.exe",
        f"del /F /S oenetlimitx64.cat",
        f"del /F /S BlackSlient.exe",
        f"cd x86",
        f"del /F /S LISSNetInfoSniffer.exe",
        f"cd ..",
    ]
    if delMtc:
        lines.append("del /F /S MultiClient.exe")
    if shutdown:
        lines.append("timeout 5")
        lines.append("shutdown /l")
    lines.append("exit")
    return "\n".join(lines)
