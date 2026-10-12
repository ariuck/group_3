from ultralytics import YOLO

def main():
    model = YOLO('yolo11n.pt')
    print('YOLO11n loaded successfully!')
    print('Class names:', model.names)

if __name__ == '__main__':
    main()
