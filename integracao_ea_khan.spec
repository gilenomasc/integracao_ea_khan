# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT


project_root = Path(SPECPATH)
icon = str(project_root / "assets" / "EA_Khan.ico")

entrypoints = [
    "main_ea",
    "main_ea_grade_save",
    "main_ea_occurrence_save",
    "main_khan",
    "main_khan_progress",
    "unify_etapas",
]

analyses = []
for index, entrypoint in enumerate(entrypoints):
    analyses.append(
        Analysis(
            [str(project_root / f"{entrypoint}.py")],
            pathex=[str(project_root)],
            binaries=[],
            datas=[(str(project_root / "queries"), "queries")] if index == 0 else [],
            hiddenimports=[],
            hookspath=[],
            hooksconfig={},
            runtime_hooks=[],
            excludes=[],
            noarchive=False,
            optimize=0,
        )
    )

pyzs = [PYZ(analysis.pure) for analysis in analyses]
exes = [
    EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name=entrypoint,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=[icon],
    )
    for entrypoint, analysis, pyz in zip(entrypoints, analyses, pyzs)
]

binaries = [item for analysis in analyses for item in analysis.binaries]
datas = [item for analysis in analyses for item in analysis.datas]

coll = COLLECT(
    *exes,
    binaries,
    datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="integracao_ea_khan",
)
