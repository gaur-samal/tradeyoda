# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TradeYoda Backend
Packages FastAPI backend into standalone executable
"""

block_cipher = None

# Analysis - find all dependencies
a = Analysis(
    ['backend/main.py'],
    pathex=[
        '.',  # Add current directory to Python path
    ],
    binaries=[],
    datas=[
        # Include default scrip master CSV
        ('api-scrip-master.csv', '.'),
    ],
    hiddenimports=[
        # FastAPI and server
        'fastapi',
        'uvicorn',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        
        # Trading APIs
        'dhanhq',
        
        # Data processing
        'pandas',
        'numpy',
        'ta',
        
        # HTTP and networking
        'requests',
        'websockets',
        
        # Logging
        'loguru',
        
        # Data validation
        'pydantic',
        'starlette',
        
        # AI/LLM providers
        'openai',
        'anthropic',
        'google.generativeai',
        
        # Config
        'python-dotenv',
        'dotenv',
        
        # Our modules - ALL src modules
        'src',
        'src.config',
        
        # src.agents - ALL agent modules
        'src.agents',
        'src.agents.data_agent',
        'src.agents.execution_agent',
        'src.agents.llm_agent',                    # Added
        'src.agents.options_agent',                # Added
        'src.agents.technical_analysis_agent',     # Added
        
        # src.utils - ALL utility modules
        'src.utils',
        'src.utils.desktop_config',
        'src.utils.logger',
        'src.utils.licensing_client',
        'src.utils.security_master',
        'src.utils.credentials_store',
        'src.utils.helpers',
        'src.utils.theta_calculator',              # Added
        
        # Root level modules
        'orchestrator',
        
        # Backend modules (backend/main.py is entry point, so it's auto-included)
        'backend.middleware',                       # Added explicitly
        'middleware',                               # Also try without backend prefix
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PIL',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ - Compress Python bytecode
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE - Create executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='tradeyoda-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console window for logs
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT - Collect all files into distribution folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='tradeyoda-backend',
)

