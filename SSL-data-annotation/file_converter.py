import os
from PIL import Image
import pillow_heif

input_folder = r"C:\Users\Digital Twingine\Desktop\chloe\label_small_data\standard20\import"
output_folder = r"C:\Users\Digital Twingine\Desktop\chloe\label_small_data\standard20\standard"
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(".heic"):
        heic_path = os.path.join(input_folder, filename)
        jpg_path = os.path.join(output_folder, os.path.splitext(filename)[0] + ".jpg")

        heif_file = pillow_heif.read_heif(heic_path)
        image = Image.frombytes(
            heif_file.mode, heif_file.size, heif_file.data, "raw"
        )
        image.save(jpg_path, "JPEG")

print("Conversion complete.")
