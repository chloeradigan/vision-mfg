import os
import json
import torch
import numpy as np
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity

# --- Config ---
reference_dir = "original_candidate_features"
candidate_dir = "yolo_candidate_features"
metadata_path = "crop_metadata.json"
output_label_dir = "yolo_pseudo_labels"
os.makedirs(output_label_dir, exist_ok=True)

similarity_threshold = 0.4  # You can tune this

# --- Load crop metadata ---
with open(metadata_path, "r") as f:
    crop_metadata = json.load(f)

# Build a lookup from crop filename to metadata
metadata_lookup = {entry["crop_filename"].replace(".jpg", ""): entry for entry in crop_metadata}

# --- Load reference features ---
reference_features = []
for fname in os.listdir(reference_dir):
    if fname.endswith(".pt"):
        vec = torch.load(os.path.join(reference_dir, fname)).numpy()
        reference_features.append(vec)
reference_matrix = np.stack(reference_features)  # [N_ref, dim]

# --- Process each candidate ---
matches_per_image = {}

for fname in tqdm(os.listdir(candidate_dir)):
    if not fname.endswith(".pt"):
        continue

    crop_id = os.path.splitext(fname)[0]
    if crop_id not in metadata_lookup:
        continue

    vec = torch.load(os.path.join(candidate_dir, fname)).numpy().reshape(1, -1)
    sims = cosine_similarity(vec, reference_matrix)
    max_sim = sims.max()

    if max_sim >= similarity_threshold:
        meta = metadata_lookup[crop_id]
        x, y, w, h = meta["bbox"]
        img_w, img_h = meta["image_size"]
        cx = (x + w / 2) / img_w
        cy = (y + h / 2) / img_h
        nw = w / img_w
        nh = h / img_h

        label_line = f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n"
        out_name = os.path.splitext(meta["source_image"])[0] + ".txt"
        out_path = os.path.join(output_label_dir, out_name)
        with open(out_path, "a") as f:
            f.write(label_line)

print(f"Pseudo-labeling complete. YOLO .txt files saved to: {output_label_dir}")
