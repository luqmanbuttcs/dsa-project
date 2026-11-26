# PyInstaller onedir build for the premium PyQt6 Solitaire application.
# Run from the repository root:
#   python -m PyInstaller --clean --noconfirm packaging/KlondikeSolitaire.spec

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT / "src"
RESOURCE_ROOT = SOURCE_ROOT / "solitaire" / "ui" / "premium" / "resources"

resource_data = []
for folder in ("art", "audio", "textures"):
    source = RESOURCE_ROOT / folder
    if not source.is_dir():
        raise FileNotFoundError(f"Required bundled resource directory is missing: {source}")
    resource_data.append(
        (str(source), f"solitaire/ui/premium/resources/{folder}")
    )

a = Analysis(
    [str(SOURCE_ROOT / "solitaire" / "main.py")],
    pathex=[str(SOURCE_ROOT)],
    binaries=[],
    datas=resource_data,
    hiddenimports=["PyQt6.QtMultimedia"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KlondikeSolitaire",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="KlondikeSolitaire",
)
