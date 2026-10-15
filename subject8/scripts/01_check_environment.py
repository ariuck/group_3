import sys
import torch
import ultralytics
from ultralytics import YOLO

def main():
    print('Python:', sys.version.split()[0])
    print('PyTorch:', torch.__version__)
    print('Ultralytics:', ultralytics.__version__)
    print('CUDA available:', torch.cuda.is_available())

    if torch.cuda.is_available():
        print('GPU:', torch.cuda.get_device_name(0))

    try:
        model = YOLO('yolo11n.pt')
        print('YOLO11n loaded successfully!')
        print('COCO Classes count:', len(model.names))
    except Exception as e:
        print('YOLO11n load error:', e)

if __name__ == '__main__':
    main()
