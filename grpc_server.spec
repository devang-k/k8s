# -*- mode: python ; coding: utf-8 -*-

import os
import subprocess

# Run the encryption script on the source folder
subprocess.run([
    "python", "encryption.py",
    "stdcell_generation_shared",
    "--keyfile", "secret.key"
], check=True)

def collect_all_files_with_structure(source_dir, target_base):
    data = []
    for root, _, files in os.walk(source_dir):
        for f in files:
            if f.endswith('.enc'):
                full_path = os.path.join(root, f)
                relative_path = os.path.relpath(root, source_dir)
                target_path = os.path.join(target_base, relative_path)
                data.append((full_path, target_path))
    return data


a1 = Analysis(
    ['grpc_server.py'],
    pathex=['./'],
    binaries=[],
    datas=[*collect_all_files_with_structure('stdcell_generation_shared', 'stdcell_generation_shared'),('tech/monCFET/mcfet.lyp', 'tech/monCFET'), ('./utils/thumbnail/thumbnail.py', 'utils/thumbnail'), ('pex_extraction/data/*', 'pex_extraction/data'), ('./version.conf', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['klayout','z3-solver'],
    noarchive=False,
    optimize=0,
)
pyz1 = PYZ(a1.pure)

exe1 = EXE(
    pyz1,
    a1.scripts,
    a1.binaries,
    a1.datas,
    [],
    name='grpc_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

a2 = Analysis(
    ['sivista.py'],
    pathex=['./'],
    binaries=[],
    datas=[('tech/monCFET/mcfet.lyp', 'tech/monCFET'), ('./utils/thumbnail/thumbnail.py', 'utils/thumbnail'), ('pex_extraction/data/*', 'pex_extraction/data'), ('./version.conf', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['klayout','z3-solver','yaspin'],
    noarchive=False,
    optimize=0,
)
pyz2 = PYZ(a2.pure)

exe2 = EXE(
    pyz2,
    a2.scripts,
    a2.binaries,
    a2.datas,
    [],
    name='sivista',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
