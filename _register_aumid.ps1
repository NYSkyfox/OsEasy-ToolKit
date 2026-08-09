# 注册 OsEasy-ToolKit 的 AppUserModelID（Toast 通知必需）
$ErrorActionPreference = 'Stop'

$APP_ID = 'OsEasy-ToolKit'
$PYW = 'C:\Program Files\Python312\python.exe'
$SCRIPT = 'g:\OsEasy-ToolKit\OsEasy-ToolKit-main\main.py'
$WORKDIR = 'g:\OsEasy-ToolKit\OsEasy-ToolKit-main'
$ICON = 'g:\OsEasy-ToolKit\OsEasy-ToolKit-main\logo.ico'
$LNK = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\OsEasy-ToolKit.lnk'

# 1) 创建快捷方式
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($LNK)
$sc.TargetPath = $PYW
$sc.Arguments = "`"$SCRIPT`""
$sc.WorkingDirectory = $WORKDIR
$sc.IconLocation = "$ICON,0"
$sc.Description = 'OsEasy-ToolKit'
$sc.Save()

# 2) 用 IPropertyStore 设置 System.AppUserModel.ID
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class ShellHelper
{
    [ComImport, Guid("00021401-0000-0000-C000-000000000046")]
    public class CShellLink { }

    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("000214F9-0000-0000-C000-000000000046")]
    public interface IShellLink { }

    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("0000010B-0000-0000-C000-000000000046")]
    public interface IPersistFile
    {
        void GetClassID(out Guid pClassID);
        int IsDirty();
        void Load(string pszFileName, int dwMode);
        void Save(string pszFileName, bool fRemember);
        void SaveCompleted(string pszFileName);
        string GetCurFile();
    }

    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")]
    public interface IPropertyStore
    {
        int GetCount(out uint cProps);
        int GetAt(uint iProp, out PROPERTYKEY pkey);
        int GetValue(ref PROPERTYKEY key, out PROPVARIANT pv);
        int SetValue(ref PROPERTYKEY key, ref PROPVARIANT pv);
        int Commit();
    }

    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    public struct PROPERTYKEY
    {
        public Guid fmtid;
        public uint pid;
    }

    [StructLayout(LayoutKind.Explicit)]
    public struct PROPVARIANT
    {
        [FieldOffset(0)] public ushort vt;
        [FieldOffset(8)] public IntPtr pointerValue;
    }

    public static void SetAppUserModelID(string lnkPath, string appId)
    {
        object linkObj = new CShellLink();
        IPersistFile pf = (IPersistFile)linkObj;
        pf.Load(lnkPath, 2); // STGM_READWRITE
        IPropertyStore store = (IPropertyStore)linkObj;
        PROPERTYKEY key = new PROPERTYKEY();
        key.fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3"); // PKEY_AppUserModel_ID
        key.pid = 5;
        PROPVARIANT pv = new PROPVARIANT();
        pv.vt = 31; // VT_LPWSTR
        pv.pointerValue = Marshal.StringToCoTaskMemUni(appId);
        store.SetValue(ref key, ref pv);
        store.Commit();
        Marshal.FreeCoTaskMem(pv.pointerValue);
        Marshal.FinalReleaseComObject(store);
        Marshal.FinalReleaseComObject(pf);
    }
}
'@

[ShellHelper]::SetAppUserModelID($LNK, $APP_ID)
"OK: 快捷方式已创建并注册 AUMID=$APP_ID"
Get-Item $LNK | Select-Object FullName, Length
