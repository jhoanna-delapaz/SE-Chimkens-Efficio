# Efficio.spec
# ─────────────────────────────────────────────────────────────────────────────
# PyInstaller build spec for the Efficio desktop application.
#
# HOW TO BUILD LOCALLY:
#   pyinstaller Efficio.spec
#
# OUTPUT:
#   dist/Efficio/Efficio.exe  (+ supporting DLLs)
#
# When adding a new module under src/, add it to `hiddenimports` below.
# ─────────────────────────────────────────────────────────────────────────────

block_cipher = None

a = Analysis(
    # Entry point
    ['src/main.py'],

    # Tell PyInstaller to treat src/ as a top-level package root,
    # so all internal imports (config, data, business, presentation) resolve.
    pathex=['src'],

    binaries=[],

    # Non-Python files to bundle (e.g. images, icons, stylesheets).
    # Format: ('source_path', 'dest_folder_inside_bundle')
    # The database file is intentionally excluded — it will be created fresh
    # in the user's AppData folder on first run via config.py.
    datas=[],

    # Modules that PyInstaller's static analyser cannot auto-discover
    # (usually due to dynamic imports or sys.path manipulation).
    hiddenimports=[
        'config',
        'data',
        'data.DataBaseHandler',
        'data.models',
        'business',
        'business.task_manager',
        'presentation',
        'presentation.dashboard',
        'presentation.task_editor_dialog',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Efficio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # No terminal window (matches --windowed flag)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Efficio',  # Output folder: dist/Efficio/
)
