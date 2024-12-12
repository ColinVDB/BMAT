# -*- mode: python ; coding: utf-8 -*-

block_cipher = None  # No encryption for bytecode.

a = Analysis(
    ['BMAT.py'],  # The main script to be analyzed.
    pathex=[],  # Additional paths to search for imports.
    binaries=[],  # Include binary files.
    datas=[('Pipelines/.gitkeep', 'Pipelines/'), 
           ('LocalPipelines/.gitkeep', 'LocalPipelines/'),
           ('Pictures', 'Pictures'),
           ('dcm2bids_sss.json', '.'),
           ('memory.xz', '.'),
           ('readme_example', '.'),
           ('sequences.csv', '.'),
           ('server_info.json', '.')],  # Include data files.
    hiddenimports=[],  # Hidden imports not detected automatically.
    hookspath=[],  # Paths to search for hook files.
    runtime_hooks=[],  # Scripts to run at the beginning of bootloader sequence.
    excludes=[],  # Modules to exclude from the analysis.
    win_no_prefer_redirects=False,  # Windows DLL redirection.
    win_private_assemblies=False,  # Windows private assemblies.
    cipher=block_cipher,  # Cipher for encrypting bytecode.
    noarchive=True  # Do not place modules in a .pyz archive.
)

pyz = PYZ(
    a.pure,  # Pure Python modules from the analysis.
    a.zipped_data,  # Compressed bytecode.
    cipher=block_cipher  # Cipher for encrypting bytecode.
)

exe = EXE(
    pyz,  # The PYZ archive.
    a.scripts,  # Scripts to execute.
    exclude_binaries=True,  # Exclude binary files from the archive.
    name='BMAT',  # Name of the executable.
    debug=False,  # Generate a debug executable.
    bootloader_ignore_signals=False,  # Bootloader signal handling.
    strip=False,  # Strip debug symbols.
    upx=True,  # Compress the executable with UPX.
    console=True,  # Console application for Windows (False for windowed).
    icon="Pictures/BMAT.ico"  # path to icon file
)

coll = COLLECT(
    exe,  # The EXE object.
    a.binaries,  # Binary files from the analysis.
    a.zipfiles,  # Zip files from the analysis.
    a.datas,  # Data files from the analysis.
    strip=False,  # Strip debug symbols.
    upx=True,  # Compress the collected files with UPX.
    upx_exclude=[],  # Files to exclude from UPX compression.
    name='BMAT'  # Name of the output directory.
)

