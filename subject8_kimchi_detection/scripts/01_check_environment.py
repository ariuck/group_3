import sys
import torch
import ultralytics

def main():
    print('Python:', sys.version.split()[0])
    print('PyTorch:', torch.__version__)
    print('Ultralytics:', ultralytics.__version__)
    print('CUDA available:', torch.cuda.is_available())

    if torch.cuda.is_available():
        print('GPU:', torch.cuda.get_device_name(0))

if __name__ == '__main__':
    main()
