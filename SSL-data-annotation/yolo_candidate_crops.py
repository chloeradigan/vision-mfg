import os
import json
from PIL import Image
from ultralytics import YOLO

# --- Paths ---
input_dir = r"C:\Users\Digital Twingine\Desktop\chloe\label_small_data\standard20\unlabeled_images"
output_dir = r"C:\Users\Digital Twingine\Desktop\chloe\method_verification\yolo_candidate_crops"
os.makedirs(output_dir, exist_ok=True)

crop_metadata = []

# --- Load pretrained YOLOv8 model (COCO-trained) ---
model = YOLO("yolov8n.pt")  # You can also use yolov8s.pt or yolov8m.pt

# --- Loop through all images ---
for filename in os.listdir(input_dir):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    image_path = os.path.join(input_dir, filename)
    image = Image.open(image_path).convert("RGB")
    w, h = image.size

    results = model(image_path, conf=0.3, iou=0.5)

    for i, box in enumerate(results[0].boxes.xyxy.cpu().numpy()):
        x1, y1, x2, y2 = map(int, box)
        bw, bh = x2 - x1, y2 - y1
        crop = image.crop((x1, y1, x2, y2))
        crop_name = f"{os.path.splitext(filename)[0]}_yolo_{i}.jpg"
        crop_path = os.path.join(output_dir, crop_name)
        crop.save(crop_path)

        crop_metadata.append({
            "crop_filename": crop_name,
            "source_image": filename,
            "bbox": [int(x1), int(y1), int(bw), int(bh)],
            "image_size": [int(w), int(h)]
        })

# --- Save metadata for pseudo-labeling ---
with open("crop_metadata.json", "w") as f:
    json.dump(crop_metadata, f, indent=2)

print(f"YOLO crops saved to '{output_dir}'")
print(f"Metadata saved to 'crop_metadata.json'")
