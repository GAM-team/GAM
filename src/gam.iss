; --- 1. PREPROCESSOR DEFINITIONS ---
#define AppVersion GetEnv("GAMVERSION")
#if AppVersion == ""
  #define AppVersion "7.0.0" 
#endif

; Pull architecture directly from GitHub Actions environment variable
#define RunnerArch GetEnv("RUNNER_ARCH")

[Setup]
; --- 2. CORE APPLICATION INFO ---
AppId={{D86B52B2-EFE9-4F9D-8BA3-9D84B9B2D319}
AppName=GAM7
AppVersion={#AppVersion}
AppPublisher=GAM Team - google-apps-manager@googlegroups.com
DefaultDirName={sd}\GAM7
LicenseFile=dist\gam\gam7\LICENSE
PrivilegesRequired=admin
ChangesEnvironment=yes

; Tell Inno Setup to use a custom signtool defined via the command line
SignTool=gamsigntool

; --- 3. COMPRESSION & OPTIMIZATION ---
Compression=lzma2/ultra64
SolidCompression=yes

; --- 4. DYNAMIC ARCHITECTURE CONFIGURATION ---
; GitHub Actions RUNNER_ARCH is typically uppercase "ARM64" or "X64"
#if RunnerArch == "ARM64" || RunnerArch == "arm64"
  ArchitecturesAllowed=arm64
  ArchitecturesInstallIn64BitMode=arm64
  OutputBaseFilename=gam-{#AppVersion}-windows-arm64
#else
  ArchitecturesAllowed=x64compatible
  ArchitecturesInstallIn64BitMode=x64compatible
  OutputBaseFilename=gam-{#AppVersion}-windows-x86_64
#endif

[Messages]
; Custom error if an admin tries to run the ARM64 installer on an Intel machine
#if RunnerArch == "ARM64" || RunnerArch == "arm64"
WindowsVersionNotSupported=You downloaded the ARM64 version of GAM, but this computer has an Intel or AMD processor.%n%nPlease go back to the release page and download the x86_64 installer instead.
#endif

[Files]
; --- 5. DYNAMIC FILE INCLUSION ---
Source: "dist\gam\gam7\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
; --- 6. PATH ENVIRONMENT VARIABLE ---
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; \
    Check: NeedsAddPath(ExpandConstant('{app}'))

[Code]
const
  ERROR_SUCCESS = 0;

function MsiEnumRelatedProducts(lpUpgradeCode: string; dwReserved: Integer; iProductIndex: Integer; lpProductBuf: string): Integer;
  external 'MsiEnumRelatedProductsW@msi.dll stdcall';

function UninstallWixMSI(): Boolean;
var
  UpgradeCode: string;
  ProductCode: string;
  ResultCode: Integer;
begin
  UpgradeCode := '{D86B52B2-EFE9-4F9D-8BA3-9D84B9B2D319}';
  ProductCode := StringOfChar(' ', 39); 
  
  ResultCode := MsiEnumRelatedProducts(UpgradeCode, 0, 0, ProductCode);
  
  if ResultCode = ERROR_SUCCESS then
  begin
    ProductCode := Trim(ProductCode);
    Exec('msiexec.exe', '/x ' + ProductCode + ' /qn /norestart', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
  
  Result := True;
end;

function InitializeSetup(): Boolean;
begin
  // --- Architecture Warning for Emulation ---
  #if RunnerArch != "ARM64" && RunnerArch != "arm64"
  if IsArm64() then
  begin
    if MsgBox('Notice: You are installing the Intel (x86_64) build of GAM on an ARM processor.' + #13#10#13#10 +
              'While this will work via Windows emulation, it will perform worse than the native ARM64 version.' + #13#10#13#10 +
              'Do you want to continue with the installation anyway?', 
              mbConfirmation, MB_YESNO) = idNo then
    begin
      Result := False; 
      Exit;
    end;
  end;
  #endif

  UninstallWixMSI();
  Result := True; 
end;

function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;
