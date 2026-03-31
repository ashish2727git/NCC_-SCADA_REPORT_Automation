# -*- mode: python ; coding: utf-8 -*-


from PyInstaller.utils.hooks import collect_all

datas_sel, binaries_sel, hiddenimports_sel = collect_all('selenium')
datas_wdm, binaries_wdm, hiddenimports_wdm = collect_all('webdriver_manager')
datas_ctk, binaries_ctk, hiddenimports_ctk = collect_all('customtkinter')

a = Analysis(
    ['NexusSyncPro_v4_Ashish.py'],
    pathex=[],
    binaries=[] + binaries_sel + binaries_wdm + binaries_ctk,
    datas=[] + datas_sel + datas_wdm + datas_ctk,
    hiddenimports=[
        'pandas',
        'openpyxl',
        'bs4',
        'requests',
        'urllib3',
        'schedule',
        'darkdetect',
        'PIL',
        'PIL._tkinter_finder',
        'dotenv',
        'customtkinter',
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.webdriver',
        'selenium.webdriver.common',
        'selenium.webdriver.common.by',
        'selenium.webdriver.common.keys',
        'selenium.webdriver.common.action_chains',
        'selenium.webdriver.support',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'webdriver_manager',
        'webdriver_manager.chrome'
    ] + hiddenimports_sel + hiddenimports_wdm + hiddenimports_ctk,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NexusSyncPro_v4_Ashish',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['nexus_logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NexusSyncPro_v4_Ashish',
)
