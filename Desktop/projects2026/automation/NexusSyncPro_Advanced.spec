# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('nexus_logo.ico', '.'), ('ncc_logo.png', '.'), ('intro video.mp4', '.')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret2 = collect_all('selenium')
datas += tmp_ret2[0]; binaries += tmp_ret2[1]; hiddenimports += tmp_ret2[2]

tmp_ret3 = collect_all('pandas')
datas += tmp_ret3[0]; binaries += tmp_ret3[1]; hiddenimports += tmp_ret3[2]

tmp_ret4 = collect_all('tkcalendar')
datas += tmp_ret4[0]; binaries += tmp_ret4[1]; hiddenimports += tmp_ret4[2]

tmp_ret5 = collect_all('babel')
datas += tmp_ret5[0]; binaries += tmp_ret5[1]; hiddenimports += tmp_ret5[2]

# Remove the mypyc-compiled uuid_utils binary from binaries list to prevent
# decompression errors at runtime (uuid_utils is pulled in transitively by
# langchain-core/langsmith but is never used by this application)
binaries = [b for b in binaries if '81d243bd' not in b[0] and 'mypyc' not in b[0].lower()]

# Also strip it from datas just in case
datas = [d for d in datas if '81d243bd' not in d[0] and ('mypyc' not in d[0].lower() or 'charset_normalizer' in d[0].lower())]

a = Analysis(
    ['NexusSyncPro_Advanced.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        'pandas',
        'pandas._libs.properties',
        'pandas._libs.interval',
        'pandas._libs.hashtable',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.offsets',
        'pandas._libs.tslibs.parsing'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # These packages are NOT used by this app but get pulled in transitively.
        # uuid_utils is compiled with mypyc/Rust and causes "decompression
        # resulted in return code -1" errors at runtime inside a PyInstaller bundle.
        'uuid_utils',
        'langchain',
        'langchain_core',
        'langchain_community',
        'langchain_text_splitters',
        'langsmith',
        'langchain_ollama',
        'langchain_classic',
        'langchain_protocol',
        'ollama',
        'streamlit',
        'altair',
        'plotly',
        'torch',
        'numba',
        'llvmlite',
        'playwright',
        'pywebview',
        'edge_tts',
        'sounddevice',
        'soundfile',
        'SpeechRecognition',
        'openai_whisper',
        'whisper',
        'sklearn',
        'scipy',
        'matplotlib',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Ashish_Kumar_NexusSyncPro_v17.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['nexus_logo.ico'],
)
