#!/usr/bin/env python3
"""
Build script for PDF Page Extractor with NAPS2 integration.

This script creates a Windows executable using PyInstaller and
builds an installer using Inno Setup that includes NAPS2 scanner software.
"""

import sys
import os
import shutil
import subprocess
import argparse
import urllib.request
import hashlib
from pathlib import Path

# NAPS2 configuration
NAPS2_VERSION = "8.2.1"
NAPS2_URL = f"https://github.com/cyanfish/naps2/releases/download/v{NAPS2_VERSION}/naps2-{NAPS2_VERSION}-win-x64.exe"
NAPS2_FILENAME = f"naps2-{NAPS2_VERSION}-win-x64.exe"
NAPS2_EXPECTED_SIZE = 50 * 1024 * 1024  # Approximate size in bytes (50MB)


def find_iscc():
    """Find the Inno Setup Compiler executable on Windows."""
    # First try using shutil.which (more reliable than subprocess on Windows)
    iscc_path = shutil.which('iscc')
    if iscc_path:
        print(f"Found iscc via shutil.which: {iscc_path}")
        return iscc_path

    # Try the exact path we know exists
    known_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if Path(known_path).exists():
        print(f"Found iscc at known location: {known_path}")
        return known_path

    # Try other common paths
    common_paths = [
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]

    for path in common_paths:
        if Path(path).exists():
            print(f"Found iscc at: {path}")
            return path

    return None


def test_iscc_executable(iscc_path):
    """Test if the ISCC executable works."""
    try:
        result = subprocess.run([iscc_path], capture_output=True, text=True, timeout=10)
        output_text = (result.stdout or '') + (result.stderr or '')

        if 'Inno Setup' in output_text and result.returncode == 1:
            print("✓ ISCC executable works correctly")
            return True
        else:
            print(f"✗ ISCC test failed - Return code: {result.returncode}")
            return False
    except Exception as e:
        print(f"✗ Error testing ISCC: {e}")
        return False


def download_file_with_progress(url, filename):
    """Download file with progress indication."""

    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100.0, (downloaded / total_size) * 100)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\rDownloading: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')
        else:
            mb_downloaded = downloaded / (1024 * 1024)
            print(f"\rDownloading: {mb_downloaded:.1f} MB", end='')

    try:
        urllib.request.urlretrieve(url, filename, progress_hook)
        print()  # New line after progress
        return True
    except Exception as e:
        print(f"\nDownload failed: {e}")
        return False


def verify_file_integrity(filepath, min_size=None):
    """Verify downloaded file integrity."""
    if not Path(filepath).exists():
        return False, "File does not exist"

    file_size = Path(filepath).stat().st_size
    if min_size and file_size < min_size:
        return False, f"File size too small: {file_size} bytes (expected at least {min_size})"

    # Check if it's a valid PE executable
    try:
        with open(filepath, 'rb') as f:
            header = f.read(2)
            if header != b'MZ':
                return False, "Not a valid Windows executable (missing MZ header)"
    except Exception as e:
        return False, f"Error reading file: {e}"

    return True, f"File verified: {file_size} bytes"


def download_naps2():
    """Download NAPS2 if not already present."""
    naps2_path = Path("third_party") / NAPS2_FILENAME

    # Create third_party directory
    naps2_path.parent.mkdir(exist_ok=True)

    if naps2_path.exists():
        print(f"NAPS2 already exists: {naps2_path}")
        # Verify existing file
        is_valid, message = verify_file_integrity(naps2_path, NAPS2_EXPECTED_SIZE * 0.8)  # Allow 20% variance
        if is_valid:
            print(f"✓ {message}")
            return True
        else:
            print(f"⚠ Existing file invalid: {message}")
            print("Re-downloading NAPS2...")
            naps2_path.unlink()  # Remove invalid file

    print(f"Downloading NAPS2 v{NAPS2_VERSION}...")
    print(f"From: {NAPS2_URL}")
    print(f"To: {naps2_path}")

    success = download_file_with_progress(NAPS2_URL, str(naps2_path))

    if success:
        # Verify downloaded file
        is_valid, message = verify_file_integrity(naps2_path, NAPS2_EXPECTED_SIZE * 0.8)
        if is_valid:
            print(f"✓ NAPS2 downloaded successfully: {message}")
            return True
        else:
            print(f"✗ Downloaded file invalid: {message}")
            naps2_path.unlink()  # Remove invalid file
            return False
    else:
        print("✗ Failed to download NAPS2")
        return False


def run_command(cmd, check=True, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def clean_build_dirs():
    """Clean previous build directories."""
    dirs_to_clean = ['build', 'dist', '__pycache__']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

    # Clean .pyc files recursively
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

    # Clean spec files from previous builds
    spec_files = ['PDFPageExtractor.spec', 'version_info.txt']
    for spec_file in spec_files:
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print(f"Removed {spec_file}")


def check_dependencies():
    """Check if required tools are available."""
    missing = []

    # Check PyInstaller
    try:
        result = subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True, timeout=10)
        print("✓ Found pyinstaller")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("✗ Missing pyinstaller")
        missing.append("pyinstaller: PyInstaller (pip install pyinstaller)")

    # Check required Python packages
    required_packages = {
        'PySide6': 'PySide6',
        'fitz': 'PyMuPDF'
    }

    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✓ Found {package_name}")
        except ImportError:
            print(f"✗ Missing {package_name}")
            missing.append(f"{package_name}: pip install {package_name}")

    # Check project structure
    required_files = ['main.py', 'src/__init__.py', 'src/ui/__init__.py']
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"✗ Missing required file: {file_path}")
            missing.append(f"Required file: {file_path}")

    # Check optional files
    optional_files = ['src/assets/icon.ico']
    for file_path in optional_files:
        if Path(file_path).exists():
            print(f"✓ Found optional file: {file_path}")
        else:
            print(f"⚠ Missing optional file: {file_path}")

    return missing


def check_iscc():
    """Check ISCC (Inno Setup Compiler) availability."""
    iscc_path = find_iscc()
    if iscc_path and test_iscc_executable(iscc_path):
        print("✓ Found and verified ISCC")
        return iscc_path
    else:
        print("✗ ISCC not found or not working")
        return None


def create_spec_file():
    """Create PyInstaller spec file with custom configuration."""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Get the project root directory
project_root = Path.cwd()

block_cipher = None

# Define data files to include
datas = []

# Add assets folder if it exists
assets_path = project_root / 'src' / 'assets'
if assets_path.exists():
    datas.append((str(assets_path), 'assets'))


# Define hidden imports for PDF processing
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'fitz',  # PyMuPDF
    'pymupdf',  # Alternative import name
    'json',
    'pathlib',
]

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unnecessary modules to reduce size
excluded_modules = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
    'sklearn',
    'pytest',
    'setuptools',
    'distutils',
    'test',
    'unittest',
]

# Filter out excluded modules
for module in excluded_modules:
    a.binaries = [x for x in a.binaries if not x[0].lower().startswith(module.lower())]
    a.datas = [x for x in a.datas if not x[0].lower().startswith(module.lower())]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Icon path - use if available, otherwise None
icon_path = project_root / 'src' / 'assets' / 'icon.ico'
icon_str = str(icon_path) if icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDFPageExtractor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, not console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_str,
    version='version_info.txt'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDFPageExtractor',
)
'''

    with open('PDFPageExtractor.spec', 'w') as f:
        f.write(spec_content.strip())


def create_version_info():
    """Create version info file for Windows executable."""
    version_info = '''
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 1, 1, 0),
    prodvers=(1, 1, 1, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Moses Oghene'),
        StringStruct(u'FileDescription', u'PDF Page Extractor - Extract and organize PDF pages with NAPS2 scanner integration'),
        StringStruct(u'FileVersion', u'1.1.1.0'),
        StringStruct(u'InternalName', u'PDFPageExtractor'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2024 Moses Oghene'),
        StringStruct(u'OriginalFilename', u'PDFPageExtractor.exe'),
        StringStruct(u'ProductName', u'PDF Page Extractor with NAPS2'),
        StringStruct(u'ProductVersion', u'1.1.1.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''

    with open('version_info.txt', 'w') as f:
        f.write(version_info.strip())


def build_executable(debug=False):
    """Build the executable using PyInstaller."""
    print("Building executable...")

    # Create spec file and version info
    create_spec_file()
    create_version_info()

    # Build command
    cmd = ['pyinstaller', 'PDFPageExtractor.spec']
    if not debug:
        cmd.extend(['--clean', '--noconfirm'])

    if debug:
        cmd.append('--debug=all')

    try:
        run_command(cmd)
        print("✓ Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to build executable: {e}")
        return False


def create_inno_script():
    """Create Inno Setup script for building the installer with NAPS2."""

    # Check if icon exists, use conditional setup
    icon_path = Path('src/assets/icon.ico')
    has_icon = icon_path.exists()

    # Check if optional files exist
    has_profiles = Path('profiles.json').exists()
    has_config_template = Path('config.json.template').exists()

    # Check if NAPS2 exists
    naps2_path = Path("third_party") / NAPS2_FILENAME
    has_naps2 = naps2_path.exists()

    print(f"Icon file exists: {has_icon}")
    print(f"Profiles file exists: {has_profiles}")
    print(f"Config template exists: {has_config_template}")
    print(f"NAPS2 installer exists: {has_naps2}")

    # Build the script dynamically based on what files exist
    inno_script = f'''
; Inno Setup Script for PDF Page Extractor with NAPS2 Scanner Integration
; Generated by build script

#define MyAppName "PDF Page Extractor"
#define MyAppVersion "1.1.1"
#define MyAppPublisher "Moses Oghene"
#define MyAppURL "https://github.com/mosesogathe/pdf-page-extractor"
#define MyAppExeName "PDFPageExtractor.exe"
#define NAPS2Version "{NAPS2_VERSION}"
#define NAPS2Installer "{NAPS2_FILENAME}"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{{{A1B2C3D4-E5F6-7890-ABCD-123456789012}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DisableProgramGroupPage=yes
OutputDir=dist\\installer
OutputBaseFilename=PDFPageExtractor-{{#MyAppVersion}}-with-NAPS2-Setup
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64'''

    # Add icon conditionally
    if has_icon:
        inno_script += '\nSetupIconFile=src\\assets\\icon.ico'

    inno_script += f'''
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Require admin privileges for NAPS2 installation
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"
Name: "installnaps2"; Description: "Install NAPS2 Scanner Software (Recommended)"; GroupDescription: "Additional Software"'''

    # Add NAPS2 task only if installer exists
    if not has_naps2:
        inno_script = inno_script.replace('Name: "installnaps2"',
                                          '; NAPS2 installer not found - task disabled\n; Name: "installnaps2"')

    inno_script += '''

[Files]
Source: "dist\\PDFPageExtractor\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs'''

    # Add optional files conditionally
    if has_profiles:
        inno_script += '\nSource: "profiles.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist'

    if has_config_template:
        inno_script += '\nSource: "config.json.template"; DestDir: "{app}"; Flags: ignoreversion'

    # Add NAPS2 installer conditionally
    if has_naps2:
        inno_script += f'\nSource: "third_party\\{NAPS2_FILENAME}"; DestDir: "{{tmp}}"; Flags: deleteafterinstall; Tasks: installnaps2'

    inno_script += '''

[Icons]
Name: "{autoprograms}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon'''

    # Add NAPS2 icons if installing
    if has_naps2:
        inno_script += '''
Name: "{autoprograms}\\NAPS2 Scanner"; Filename: "{autopf}\\NAPS2\\NAPS2.exe"; Tasks: installnaps2
Name: "{autodesktop}\\NAPS2 Scanner"; Filename: "{autopf}\\NAPS2\\NAPS2.exe"; Tasks: desktopicon installnaps2'''

    inno_script += '''

[Run]
; Install NAPS2 silently if selected'''

    if has_naps2:
        inno_script += f'''
Filename: "{{tmp}}\\{NAPS2_FILENAME}"; Parameters: "/VERYSILENT /NORESTART /SUPPRESSMSGBOXES"; WorkingDir: "{{tmp}}"; Flags: waituntilterminated; Tasks: installnaps2; StatusMsg: "Installing NAPS2 Scanner..."'''

    inno_script += '''
; Launch PDF Page Extractor after installation
Filename: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption := 'This will install PDF Page Extractor with optional NAPS2 scanner integration.' + #13#10#13#10 +
    'NAPS2 is a document scanning application that works perfectly with PDF Page Extractor for creating and organizing scanned documents.' + #13#10#13#10 +
    'Click Next to continue, or Cancel to exit Setup.';
end;

function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    if (IsUpgrade()) then
    begin
      UnInstallOldVersion();
    end;
  end;
end;
'''

    # Ensure the installer output directory exists
    installer_dir = Path('dist/installer')
    installer_dir.mkdir(parents=True, exist_ok=True)

    with open('PDFPageExtractor.iss', 'w') as f:
        f.write(inno_script.strip())

    print("✓ Created Inno Setup script with NAPS2 integration")


def build_installer():
    """Build the installer using Inno Setup."""
    print("Building installer with NAPS2 integration...")

    # Find ISCC path
    iscc_path = find_iscc()
    if not iscc_path:
        print("✗ ISCC not found. Cannot build installer.")
        return False

    # Verify executable exists
    exe_path = Path('dist/PDFPageExtractor/PDFPageExtractor.exe')
    if not exe_path.exists():
        print(f"✗ Executable not found at: {exe_path}")
        print("  Build the executable first before creating installer.")
        return False

    # Create Inno Setup script
    create_inno_script()

    # Build installer with better error handling
    try:
        cmd = [iscc_path, 'PDFPageExtractor.iss']
        print(f"Running: {' '.join(cmd)}")

        # Run with more detailed output capture
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            timeout=300  # 5 minute timeout
        )

        # Print output for debugging
        if result.stdout:
            print("ISCC Output:")
            print(result.stdout)

        if result.stderr:
            print("ISCC Errors:")
            print(result.stderr)

        if result.returncode == 0:
            print("✓ Installer with NAPS2 built successfully!")

            # Check if NAPS2 was included
            naps2_path = Path("third_party") / NAPS2_FILENAME
            if naps2_path.exists():
                file_size = naps2_path.stat().st_size / (1024 * 1024)
                print(f"✓ NAPS2 v{NAPS2_VERSION} included ({file_size:.1f} MB)")

            return True
        else:
            print(f"✗ ISCC failed with return code: {result.returncode}")

            # Common ISCC error codes
            error_messages = {
                1: "Invalid command line parameters or general error",
                2: "Compile terminated due to preprocessor or script error",
                3: "Setup executable could not be created",
                4: "Compile terminated due to internal error"
            }

            if result.returncode in error_messages:
                print(f"  Meaning: {error_messages[result.returncode]}")

            return False

    except subprocess.TimeoutExpired:
        print("✗ ISCC process timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"✗ Unexpected error running ISCC: {e}")
        return False


def create_config_template():
    """Create a configuration template file for the PDF extractor."""
    template = {
        "app_settings": {
            "theme": "light",
            "auto_save_profiles": True,
            "thumbnail_cache_size": 100,
            "remember_last_folders": True,
            "default_output_folder": "",
            "auto_load_last_session": False,
            "naps2_integration": True,
            "naps2_path": ""
        },
        "window_settings": {
            "geometry": {},
            "splitter_sizes": [800, 600],
            "last_input_folder": "",
            "last_output_folder": ""
        },
        "scanner_settings": {
            "default_profile": "Document",
            "auto_process_scans": True,
            "scan_to_temp": True
        },
        "recent_folders": [],
        "version": "1.1.1"
    }

    import json
    with open('config.json.template', 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=4)

    print("✓ Created config template with NAPS2 integration settings")


def create_sample_profiles():
    """Create sample index profiles for users."""
    profiles = [
        {
            "name": "Scanned Documents",
            "description": "For documents scanned with NAPS2",
            "fields": [
                {
                    "name": "Document Type",
                    "value": "",
                    "placeholder": "e.g., contract, receipt, form",
                    "required": True,
                    "field_type": "dropdown",
                    "options": ["Contract", "Receipt", "Invoice", "Form", "Letter", "Report", "Other"]
                },
                {
                    "name": "Date",
                    "value": "",
                    "placeholder": "YYYY-MM-DD",
                    "required": False,
                    "field_type": "text",
                    "options": []
                },
                {
                    "name": "Description",
                    "value": "",
                    "placeholder": "Brief description",
                    "required": True,
                    "field_type": "text",
                    "options": []
                }
            ],
            "output_pattern": "Scanned/{document_type}/{date}/{description}",
            "input_folder": "",
            "output_folder": ""
        },
        {
            "name": "Basic Document",
            "description": "Simple document extraction with basic metadata",
            "fields": [
                {
                    "name": "Document Type",
                    "value": "",
                    "placeholder": "e.g., contracts, invoices, reports",
                    "required": True,
                    "field_type": "text",
                    "options": []
                },
                {
                    "name": "File Name",
                    "value": "",
                    "placeholder": "Output filename (without extension)",
                    "required": True,
                    "field_type": "text",
                    "options": []
                }
            ],
            "output_pattern": "{document_type}/{file_name}",
            "input_folder": "",
            "output_folder": ""
        },
        {
            "name": "Invoice Processing",
            "description": "Organize invoices by vendor and date",
            "fields": [
                {
                    "name": "Vendor",
                    "value": "",
                    "placeholder": "Vendor or company name",
                    "required": True,
                    "field_type": "text",
                    "options": []
                },
                {
                    "name": "Invoice Number",
                    "value": "",
                    "placeholder": "Invoice number or ID",
                    "required": True,
                    "field_type": "text",
                    "options": []
                },
                {
                    "name": "Year",
                    "value": "2024",
                    "placeholder": "Invoice year",
                    "required": True,
                    "field_type": "text",
                    "options": []
                },
                {
                    "name": "Month",
                    "value": "",
                    "placeholder": "Invoice month (01-12)",
                    "required": True,
                    "field_type": "dropdown",
                    "options": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
                }
            ],
            "output_pattern": "Invoices/{vendor}/{year}/{month}/{invoice_number}",
            "input_folder": "",
            "output_folder": ""
        }
    ]

    import json
    with open('profiles.json', 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=4)

    print("✓ Created sample profiles including NAPS2 scanning profile")


def validate_project_structure():
    """Validate that all required project files are present."""
    print("Validating project structure...")

    # Check dependencies first
    missing_deps = check_dependencies()
    if missing_deps:
        print("✗ Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        return False

    # Check for ISCC
    iscc_path = check_iscc()
    if not iscc_path:
        print("✗ ISCC not available for installer creation")
        print("  Download from: https://jrsoftware.org/isinfo.php")
        return False

    print("✓ Project structure validation passed")
    return True


def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description='Build PDF Page Extractor with NAPS2')
    parser.add_argument('--clean', action='store_true', help='Clean build directories first')
    parser.add_argument('--debug', action='store_true', help='Build in debug mode')
    parser.add_argument('--no-installer', action='store_true', help='Skip installer creation')
    parser.add_argument('--installer-only', action='store_true', help='Only build installer (skip executable)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate project structure')
    parser.add_argument('--create-templates', action='store_true', help='Create config and profile templates')
    parser.add_argument('--download-naps2', action='store_true', help='Only download NAPS2 (no build)')
    parser.add_argument('--skip-naps2', action='store_true', help='Skip NAPS2 download and integration')

    args = parser.parse_args()

    # Change to script directory
    os.chdir(Path(__file__).parent)

    print("PDF Page Extractor with NAPS2 - Build Script")
    print("=" * 50)

    # Handle validate-only option
    if args.validate_only:
        success = validate_project_structure()
        return 0 if success else 1

    # Handle create-templates option
    if args.create_templates:
        create_config_template()
        create_sample_profiles()
        return 0

    # Handle download-naps2 option
    if args.download_naps2:
        success = download_naps2()
        return 0 if success else 1

    # Clean if requested
    if args.clean:
        clean_build_dirs()

    # Validate project structure
    if not validate_project_structure():
        print("✗ Project validation failed. Cannot proceed with build.")
        return 1

    # Download NAPS2 unless skipped
    if not args.skip_naps2:
        print("\n" + "-" * 30)
        print("Downloading NAPS2...")
        print("-" * 30)
        naps2_success = download_naps2()
        if not naps2_success:
            print("⚠ NAPS2 download failed. Continuing without NAPS2 integration.")
            print("  You can download it later with: python build.py --download-naps2")
    else:
        print("⚠ Skipping NAPS2 download as requested")

    success = True

    # Build executable unless installer-only
    if not args.installer_only:
        print("\n" + "-" * 30)
        print("Building executable...")
        print("-" * 30)
        success = build_executable(debug=args.debug)

    # Build installer if executable succeeded and not disabled
    if success and not args.no_installer:
        print("\n" + "-" * 30)
        print("Building installer...")
        print("-" * 30)
        # Check if executable exists (either just built or from previous build)
        exe_path = Path('dist/PDFPageExtractor/PDFPageExtractor.exe')
        if exe_path.exists():
            success = build_installer()
        else:
            print("✗ Executable not found. Cannot build installer.")
            print("  Build the executable first or use --installer-only after building.")
            success = False

    print("\n" + "=" * 50)
    if success:
        print("✓ Build completed successfully!")

        # Show what was built
        if Path('dist/PDFPageExtractor/PDFPageExtractor.exe').exists():
            exe_size = Path('dist/PDFPageExtractor/PDFPageExtractor.exe').stat().st_size / (1024 * 1024)
            print(f"✓ Executable: dist/PDFPageExtractor/PDFPageExtractor.exe ({exe_size:.1f} MB)")

        installer_files = list(Path('dist/installer').glob('*.exe'))
        if installer_files:
            installer_size = installer_files[0].stat().st_size / (1024 * 1024)
            print(f"✓ Installer: {installer_files[0]} ({installer_size:.1f} MB)")

        # Check NAPS2 integration status
        naps2_path = Path("third_party") / NAPS2_FILENAME
        if naps2_path.exists():
            naps2_size = naps2_path.stat().st_size / (1024 * 1024)
            print(f"✓ NAPS2 v{NAPS2_VERSION} included ({naps2_size:.1f} MB)")
        else:
            print("⚠ NAPS2 not included in installer")

        print("\nUsage:")
        print("- Run the installer as Administrator for system-wide installation")
        print("- The installer will optionally install NAPS2 scanner software")
        print("- Or run the executable directly from dist/PDFPageExtractor/")

        # Show template creation option
        if not Path('profiles.json').exists() or not Path('config.json.template').exists():
            print("\nOptional:")
            print("- Run with --create-templates to generate sample configuration files")

        print("\nNAPS2 Integration:")
        print("- NAPS2 will be installed to scan documents directly")
        print("- Use NAPS2 to scan → save as PDF → load in PDF Page Extractor")
        print("- Perfect workflow for document digitization and organization")

    else:
        print("✗ Build failed!")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())