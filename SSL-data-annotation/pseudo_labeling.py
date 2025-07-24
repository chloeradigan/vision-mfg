import os
import torch
import open_clip
from PIL import Image
from tqdm import tqdm
from shutil import copyfile
import torch.nn.functional as F

# Set paths
labeled_features_dir = "clip_features"
labeled_labels_dir = "standard20/labels"
unlabeled_images_dir = "standard20/unlabeled_images"
pseudo_labels_output_dir = "pseudo_labels"
os.makedirs(pseudo_labels_output_dir, exist_ok=True)

# Load CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
model = model.to(device)
model.eval()

# Load all labeled features into memory
labeled_features = {}
for filename in os.listdir(labeled_features_dir):
	if filename.endswith(".pt"):
		stem = os.path.splitext(filename)[0]
		path = os.path.join(labeled_features_dir, filename)
		feature = torch.load(path)
		labeled_features[stem] = F.normalize(feature, dim=0)

# Helper to get image CLIP embedding
def extract_clip_feature(image_path):
	image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
	with torch.no_grad():
		feature = model.encode_image(image).squeeze(0).cpu()
		feature = F.normalize(feature,dim=0)
	return feature

# Loop through all unlabeled images
for image_filename in tqdm(os.listdir(unlabeled_images_dir)):
	if image_filename.lower().endswith((".jpg", ".jpeg", ".png")):
		image_path = os.path.join(unlabeled_images_dir, image_filename)
		unlabeled_feature = extract_clip_feature(image_path)

		# Find most similar label image
		best_match = None
		best_score = -1
		for labeled_name, labeled_feature in labeled_features.items():
			score = torch.dot(unlabeled_feature, labeled_feature).item()
			if score > best_score:
				best_score = score
				best_match = labeled_name

		# Copy the best-matching label file as pseudo-label
		scr_label_path = os.path.join(labeled_labels_dir, best_match + ".txt")
		dst_label_path = os.path.join(pseudo_labels_output_dir, os.path.splitext(image_filename)[0] + ".txt")
		if os.path.exists(scr_label_path):
			copyfile(scr_label_path, dst_label_path)

print(f"Pseudo-labels saved to {pseudo_labels_output_dir}/")