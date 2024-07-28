# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('src/static/css', 'static/css'),
        ('src/static/img', 'static/img'),
        ('src/static', 'static'),
        ('src/templates', 'src/templates'),
    ],
    hiddenimports=[
        'fastapi',
        'fastapi_cli',
        'fastapi_users',
        'fastapi_users_db_sqlalchemy',
        'greenlet',
        'h11',
        'httpcore',
        'httptools',
        'httpx',
        'idna',
        'makefun',
        'mdurl',
        'orjson',
        'packaging',
        'pefile',
        'pwdlib',
        'pycparser',
        'pydantic',
        'pydantic_core',
        'rich',
        'shellingham',
        'sniffio',
        'starlette',
        'typer',
        'typing_extensions',
        'ujson',
        'uvicorn',
        'watchfiles',
        'websockets',
        'aiomysql',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ISPU_VR_FastAPI_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ISPU_VR_FastAPI_Server'
)
