# YourAppName.spec
# -*- mode: python ; coding: utf-8 -*-

import os
import cv2 # 用于获取 cv2.__file__
import fer # 用于获取 fer.__file__
import facenet_pytorch # 用于获取 facenet_pytorch.__file__

block_cipher = None

# --- 定义数据文件 ---
app_datas = [
    # Flask templates and static files
    ('templates', 'templates'),
    ('static', 'static'),
    
    # OpenCV Haar Cascade (动态路径)
    (os.path.join(os.path.dirname(cv2.__file__), 'data', 'haarcascade_frontalface_default.xml'), os.path.join('cv2', 'data')),
    
    # FER 的情绪模型数据 (动态路径, .hdf5 文件在 fer/data/ 下)
    (os.path.join(os.path.dirname(fer.__file__), 'data'), os.path.join('fer', 'data')),
    
    # facenet-pytorch 的 MTCNN 模型文件 (.pt 文件在 facenet_pytorch/data/ 下)
    (os.path.join(os.path.dirname(facenet_pytorch.__file__), 'data'), os.path.join('facenet_pytorch', 'data'))
]

# --- 定义隐藏导入 ---
app_hiddenimports = [
    'waitress',               # WSGI 服务器
    
    # facenet-pytorch 和 PyTorch 相关
    'facenet_pytorch',
    'facenet_pytorch.models.mtcnn',
    'facenet_pytorch.models.utils.detect_face', # 另一个 facenet_pytorch 内部模块
    'torch',
    'torchvision',
    'torch.nn.functional',
    'torch.utils.data', # 常见的 torch 子模块
    'torch.utils.model_zoo',
    'PIL', # Pillow，通常 torch 和 torchvision 依赖
    'PIL.Image', # 有时需要显式导入 Image
    
    # TensorFlow/Keras 相关 (如果 FER 的情绪模型是 TF/Keras 格式，则可能需要)
    # 如果 FER 的 .hdf5 模型确实是 Keras 格式，以下这些可能需要取消注释
    # 'tensorflow', # 如果需要 TensorFlow
    # 'h5py',       # 用于加载 .hdf5 Keras 模型
    # 'keras',      # 如果 FER 直接用了独立的 Keras
    # 'tensorflow.keras', # 如果用的是 tf.keras
    # 'sklearn.utils._weight_vector', # 如果 TF/Keras 依赖它

    # LZ4 (如果 FER 或其任何其他依赖项间接使用了 .lz4 压缩文件)
    # 'lz4',
    # 'lz4.block',
]

a = Analysis(
    ['app.py'],
    pathex=['D:\\project\\pyproject\\face'], 
    binaries=[],
    datas=app_datas,
    hiddenimports=app_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [], 
    exclude_binaries=True, 
    name='YourAppName',
    debug=False, # 最终发布时可以设为 False，调试时可以设为 True
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, # 将 UPX 设为 False 开始，UPX 有时会导致问题，成功后再尝试开启
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, 
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
    upx=False, # 同上
    upx_exclude=[],
    name='YourAppName'
)