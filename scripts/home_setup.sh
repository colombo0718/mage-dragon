#!/bin/bash
# 在 home 上執行：安裝相依 + 啟動 T2V script
cd C:/Users/88697/Documents
echo "=== Checking Python packages ==="
pip install --quiet diffusers transformers accelerate imageio imageio-ffmpeg 2>&1 | tail -5
echo "=== Versions ==="
python -c "import torch, diffusers; print('torch', torch.__version__); print('diffusers', diffusers.__version__); print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')"
echo "=== Starting T2V script ==="
mkdir -p video-tests
python home_diffusers_t2v.py > video-tests/run.log 2>&1 &
echo "PID: $!"
echo "Log: C:/Users/88697/Documents/video-tests/run.log"
