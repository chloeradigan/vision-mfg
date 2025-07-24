import os
from PIL import Image
import torch
import open_clip
from tqdm import tqdm
from torchvision import transforms
from torchvision.transforms.functional import pad

# Set path
image_dir = r"C:\Users\Digital Twingine\Desktop\chloe\method_verification\yolo_candidate_crops"
output_dir = r"C:\Users\Digital Twingine\Desktop\chloe\method_verification\yolo_candidate_features"
os.makedirs(output_dir, exist_ok=True)

# Load CLIP model
device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
model = model.to(device)
model.eval()

def pad_to_square(image):
		w, h = image.size
		max_dim = max(w, h)
		padding = (
			(max_dim - w) // 2, #left
			(max_dim - h) // 2, #top
			(max_dim - w + 1) // 2, #right
			(max_dim - h + 1) // 2 #bottom
		)
		return pad(image, padding, fill=0, padding_mode='constant')

custom_preprocess = transforms.Compose([
	transforms.Lambda(pad_to_square),
	transforms.Resize((224, 224)),
	transforms.ToTensor(),
	transforms.Normalize(
		mean = (0.48145466, 0.4578275, 0.40821073),
        std=(0.26862954, 0.26130258, 0.27577711)
	)
])

def extract_and_save_feature(image_path, output_path):
	image = custom_preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
	with torch.no_grad():
		feature = model.encode_image(image)
		feature = feature.cpu().squeeze(0)
		torch.save(feature, output_path)

# Loop through all images and extract features
for filename in tqdm(os.listdir(image_dir)):
	if filename.endswith((".jpg", ".png", ".jpeg")):
		image_path = os.path.join(image_dir, filename)
		output_path = os.path.join(output_dir, filename.replace('.jpg', '.pt'))
		extract_and_save_feature(image_path, output_path)

print(f"Features saved in {output_dir}/")