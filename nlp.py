import torch

# This is the key check:
is_available = torch.cuda.is_available()

print(f"Is CUDA (GPU) available? {is_available}")

if is_available:
    print(f"Device count: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
else:
    print("PyTorch cannot find your GPU. Check drivers and installation.")