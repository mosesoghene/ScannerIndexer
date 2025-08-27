#!/usr/bin/env python3
"""
Build script for PDF Page Extractor.

This script creates a Windows executable using PyInstaller and
optionally builds an installer using Inno Setup.
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path


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

# Add any existing config files
config_files = ['profiles.json']
for config_file in config_files:
    config_path = project_root / config_file
    if config_path.exists():
        datas.append((str(config_path), '.'))

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
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
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
        StringStruct(u'FileDescription', u'PDF Page Extractor - Extract and organize PDF pages'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'PDFPageExtractor'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2024 Moses Oghene'),
        StringStruct(u'OriginalFilename', u'PDFPageExtractor.exe'),
        StringStruct(u'ProductName', u'PDF Page Extractor'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
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
    """Create Inno Setup script for building the installer."""

    # Check if icon exists, use conditional setup
    icon_path = Path('src/assets/icon.ico')
    has_icon = icon_path.exists()

    # Check if optional files exist
    has_profiles = Path('profiles.json').exists()
    has_config_template = Path('config.json.template').exists()

    print(f"Icon file exists: {has_icon}")
    print(f"Profiles file exists: {has_profiles}")
    print(f"Config template exists: {has_config_template}")

    # Build the script dynamically based on what files exist
    inno_script = '''
; Inno Setup Script for PDF Page Extractor
; Generated by build script

#define MyAppName "PDF Page Extractor"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Moses Oghene"
#define MyAppURL "https://github.com/mosesogathe/pdf-page-extractor"
#define MyAppExeName "PDFPageExtractor.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{A1B2C3D4-E5F6-7890-ABCD-123456789012}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist\\installer
OutputBaseFilename=PDFPageExtractor-{#MyAppVersion}-Setup'''

    # Add icon conditionally
    if has_icon:
        inno_script += '\nSetupIconFile=src\\assets\\icon.ico'

    inno_script += '''
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\\PDFPageExtractor\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs'''

    # Add optional files conditionally
    if has_profiles:
        inno_script += '\nSource: "profiles.json"; DestDir: "{app}"; Flags: ignoreversion'

    if has_config_template:
        inno_script += '\nSource: "config.json.template"; DestDir: "{app}"; Flags: ignoreversion'

    inno_script += '''

[Icons]
Name: "{autoprograms}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
'''

    # Ensure the installer output directory exists
    installer_dir = Path('dist/installer')
    installer_dir.mkdir(parents=True, exist_ok=True)

    with open('PDFPageExtractor.iss', 'w') as f:
        f.write(inno_script.strip())

    print("✓ Created Inno Setup script")


def build_installer():
    """Build the installer using Inno Setup."""
    print("Building installer...")

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
            print("✓ Installer built successfully!")
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

            # Check if the .iss file exists and is readable
            iss_file = Path('PDFPageExtractor.iss')
            if iss_file.exists():
                print(f"✓ Inno Setup script exists: {iss_file}")
                print("  First few lines of the script:")
                try:
                    with open(iss_file, 'r') as f:
                        lines = f.readlines()[:10]
                        for i, line in enumerate(lines, 1):
                            print(f"    {i:2}: {line.rstrip()}")
                except Exception as e:
                    print(f"  Could not read script file: {e}")
            else:
                print("✗ Inno Setup script was not created")

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
            "auto_load_last_session": False
        },
        "window_settings": {
            "geometry": {},
            "splitter_sizes": [800, 600],
            "last_input_folder": "",
            "last_output_folder": ""
        },
        "recent_folders": [],
        "version": "1.0.0"
    }

    import json
    with open('config.json.template', 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=4)

    print("✓ Created config template with default settings")


def create_sample_profiles():
    """Create sample index profiles for users."""
    profiles = [
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
        },
        {
            "name": "Contract Management",
            "description": "Organize contracts by type and client",
            "fields": [
                {
                    "name": "Contract Type",
                    "value": "",
                    "placeholder": "Type of contract",
                    "required": True,
                    "field_type": "dropdown",
                    "options": ["Service Agreement", "NDA", "Employment", "Vendor", "Partnership", "License"]
                },
                {
                    "name": "Client",
                    "value": "",
                    "placeholder": "Client or counterparty name",
                    "required": True,
                    "field_type": "text",
                    "options": []
                },
                {
                    "name": "Date Signed",
                    "value": "",
                    "placeholder": "Date contract was signed",
                    "required": False,
                    "field_type": "text",
                    "options": []
                },
                {
                    "name": "File Name",
                    "value": "",
                    "placeholder": "Contract filename",
                    "required": True,
                    "field_type": "text",
                    "options": []
                }
            ],
            "output_pattern": "Contracts/{contract_type}/{client}/{file_name}",
            "input_folder": "",
            "output_folder": ""
        }
    ]

    import json
    with open('profiles.json', 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=4)

    print("✓ Created sample profiles for users")


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
    parser = argparse.ArgumentParser(description='Build PDF Page Extractor')
    parser.add_argument('--clean', action='store_true', help='Clean build directories first')
    parser.add_argument('--debug', action='store_true', help='Build in debug mode')
    parser.add_argument('--no-installer', action='store_true', help='Skip installer creation')
    parser.add_argument('--installer-only', action='store_true', help='Only build installer (skip executable)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate project structure')
    parser.add_argument('--create-templates', action='store_true', help='Create config and profile templates')

    args = parser.parse_args()

    # Change to script directory
    os.chdir(Path(__file__).parent)

    print("PDF Page Extractor Build Script")
    print("=" * 40)

    # Handle validate-only option
    if args.validate_only:
        success = validate_project_structure()
        return 0 if success else 1

    # Handle create-templates option
    if args.create_templates:
        create_config_template()
        create_sample_profiles()
        return 0

    # Clean if requested
    if args.clean:
        clean_build_dirs()

    # Validate project structure
    if not validate_project_structure():
        print("✗ Project validation failed. Cannot proceed with build.")
        return 1

    success = True

    # Build executable unless installer-only
    if not args.installer_only:
        success = build_executable(debug=args.debug)

    # Build installer if executable succeeded and not disabled
    if success and not args.no_installer:
        # Check if executable exists (either just built or from previous build)
        exe_path = Path('dist/PDFPageExtractor/PDFPageExtractor.exe')
        if exe_path.exists():
            success = build_installer()
        else:
            print("✗ Executable not found. Cannot build installer.")
            print("  Build the executable first or use --installer-only after building.")
            success = False

    print("\n" + "=" * 40)
    if success:
        print("✓ Build completed successfully!")

        # Show what was built
        if Path('dist/PDFPageExtractor/PDFPageExtractor.exe').exists():
            print(f"✓ Executable: dist/PDFPageExtractor/PDFPageExtractor.exe")

        installer_files = list(Path('dist/installer').glob('*.exe'))
        if installer_files:
            print(f"✓ Installer: {installer_files[0]}")

        print("\nUsage:")
        print("- Run the installer as Administrator for system-wide installation")
        print("- Or run the executable directly from dist/PDFPageExtractor/")

        # Show template creation option
        if not Path('profiles.json').exists() or not Path('config.json.template').exists():
            print("\nOptional:")
            print("- Run with --create-templates to generate sample configuration files")

    else:
        print("✗ Build failed!")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())