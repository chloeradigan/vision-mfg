# Semi-Supervised Visual Labeling Pipeline

This repository contains a modular pipeline for generating and validating pseudo-labels on unlabeled image data using CLIP embeddings, YOLO detection, and manual curation. The goal is to reduce the burden of manual labeling in computer vision workflows by using similarity-based labeling and visual review. Note, this work is for images of objects not yet commonly seen by models, but those seen in manufacturing, such as tool identification, stock shape ID, and machine/process classifications. 

Validation will be performed on standard benchmark datasets (e.g. Pascal VOC or COCO), using a subset of images held out from training. To simulate pseudo-labeling on unfamiliar objects, all previously learned weights for object categories will be frozen, minimizing inherited model knowledge and approximating the performance on truly unlabled or novel classes. 

Evaluation will be based on the following metrics:
- mAP@IoU thresholds
- Precision
- Recall
- F1-score

This setup measures how effectively the pipeline proposes candidate objects, filters via visual review, and assigns meaningful labels, particularly in low-supervision or novel class scenarios. 

## WARNING
This pipeline is designed to run efficiently on systems with the following:
- GPU with CUDA support (e.g. NVIDIA RTX 20XX or higher)
  
  _Used for CLIP feature extraction and YOLOv8 inference._
- Minimum 16 GB RAM
  
  _Recommended for handling image batches and candidate crops._
- Sufficient disk space
  
  _Expect temporary storage of cropped images, embeddings, and label fiels._

Running on CPU is possible but significantly slower and may result in out-of-memory errors during CLIP inference. 

## Project Notes
This is an early-stage pipeline and is currently structured as a set of modular scripts for transparency and testing. Admittedly, the overall setup is hefty, and future versions will consolidate tasks into callable functions and streamlined workflows to improve maintainability and scalability. 


## Pipeline Overview

```mermaid
graph TD
    A[Unlabeled Images] --> B[YOLOv8 Candidate Crops]
    B --> C[CLIP Feature Extraction]
    C --> D[Nearest Match to Labeled Embeddings]
    D --> E[Pseudo-Labels Generated]
    E --> F[Manual Review - keep or discard]
    F --> G[Cropped + Labeled Objects for Training]
```

## Scripts

| Script | Purpose |
|--------|---------|
| `extract_frames.py` | Extract frames evenly from a video for dataset generation |
| `file_converter.py` | Convert `.heic` images to `.jpg` |
| `crop_images.py` | Crop COCO format labeled images to reduce backround noise while training |
| `yolo_candidate_crops.py` | Use pretrained YOLOv8 to crop candidate objects |
| `extract_clip_features.py` | Feature extraction of objects produced from both labeled and unlabeled images|
| `cosine_similariy.py` | Determines feature similarity between labeled images and unlabeled images to assign pseudo labels|
| `pseudo_labeling.py` | Assign pseudo-labels to new images using CLIP similarity |
| `datavalidation.py` | GUI tool to manually approve or discard YOLO pseudo-labels |

## Folder Structure (Expected)

```
standard20/
├── standard/                  # Labeled images and labels
│   ├── standard_images/
│   └── standard_labels/
├── import/                   # Raw .heic files for conversion
├── unlabeled_images/        # Raw images for pseudo-labeling

method_verification/
├── yolo_candidate_crops/     # YOLO-generated object crops
├── yolo_pseudo_labels/       # Initial pseudo-labels from CLIP similarity
├── verified_images/          # User-kept images during manual review
├── verified_labels/          # Matched labels
├── difficult_images/         # Discarded images
├── bad_pseudo_labels/        # Discarded labels
```

## Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

Example packages used:
- `torch`, `open_clip_torch`, `tqdm`
- `opencv-python`, `Pillow`, `ultralytics`
- `pillow-heif` (for `.heic` conversion)

## Author

Chloe Radigan
