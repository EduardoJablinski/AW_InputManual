import platform

block_cipher = None

a = Analysis(
    ["aw_watcher_quattrod/__main__.py"],
    pathex=[],
    binaries=[("aw_watcher_quattrod/aw-watcher-quattrod-macos", "aw_watcher_quattrod")] if platform.system() == "Darwin" else [],
    datas=[
        ("aw_watcher_quattrod/printAppStatus.jxa", "aw_watcher_quattrod"),
        ("aw_watcher_quattrod/templates/manual_input.html", "templates"),
        ("aw_watcher_quattrod/Static/Logo quattroD.png", "Static"),
    ],
    hiddenimports=[
    '_frozen_importlib_external',
    '_frozen_importlib',
    'org',
    'pwd',
    'grp',
    'posix',
    'resource',
    'org.python',
    '_scproxy',
    'termios',
    'java.lang',
    'multiprocessing.BufferTooShort',
    'multiprocessing.AuthenticationError',
    '_posixshmem',
    '_posixsubprocess',
    'multiprocessing.get_context',
    'ctypes._CData',
    'multiprocessing.TimeoutError',
    'fcntl',
    'multiprocessing.set_start_method',
    'multiprocessing.get_start_method',
    'multiprocessing.Queue',
    'pyimod02_importers',
    '_manylinux',
    'asyncio.DefaultEventLoopPolicy',
    'pyparsing',
    'railroad',
    'readline',
    'pkg_resources.extern.pyparsing',
    'pkg_resources.extern.importlib_resources',
    'pkg_resources.extern.more_itertools',
    'com.sun',
    'com',
    'win32com.gen_py',
    '_winreg',
    'pkg_resources.extern.packaging',
    'pkg_resources.extern.appdirs',
    'pkg_resources.extern.jaraco',
    'vms_lib',
    'java',
    'StringIO',
    'PIL.Image',
    'Xlib.ext',
    'Xlib',
    'Xlib.display',
    'logger',
    'PIL',
    'numpy.ctypeslib',
    'numpy',
    'extra_tests',
    'Xlib.XK',
    'jnius',
    'simplejson',
    'dummy_threading',
    'zstandard',
    'brotli',
    'brotlicffi',
    'socks',
    'cryptography',
    'OpenSSL.crypto',
    'cryptography.x509',
    'OpenSSL',
    'chardet',
    'pyodide',
    'js',
    'pymysql',
    'dbutils',
    'Queue',
    'jinja2',
],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="aw-watcher-quattrod",
    debug=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="aw-watcher-quattrod",
)
