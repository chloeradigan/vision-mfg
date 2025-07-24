import cv2
import os
import shutil

# Config
image_dir = r"C:\Users\Digital Twingine\Desktop\chloe\method_verification\yolo_candidate_crops" #psuedo images to review
label_dir =  r"C:\Users\Digital Twingine\Desktop\chloe\method_verification\yolo_pseudo_labels" #pseudo labels to review
discard_label_dir = r"C:\Users\Digital Twingine\Desktop\chloe\method_verification\bad_pseudo_labels" #pseudo labels to discard
discard_image_dir = r"C:\Users\Digital Twingine\Desktop\chloe\method_verification\difficult_images" #unlabeled images
verified_image_dir = r"C:\Users\Digital Twingine\Desktop\chloe\method_verification\verified_images"
verified_label_dir = r"C:\Users\Digital Twingine\Desktop\chloe\method_verification\verified_labels"

os.makedirs(discard_label_dir, exist_ok=True)
os.makedirs(discard_image_dir, exist_ok=True)
os.makedirs(verified_image_dir, exist_ok=True)
os.makedirs(verified_label_dir, exist_ok=True)

def draw_yolo_boxes(image, label_path):
	h, w = image.shape[:2]
	if not os.path.exists(label_path):
		return image
	with open(label_path, 'r') as f:
		for line in f:
			parts = line.strip().split()
			if len(parts) != 5:
				continue
			cls, x_center, y_center, box_width, box_height = map(float, parts)
			x1 = int((x_center - box_width / 2) * w)
			y1 = int((y_center - box_height / 2) * h)
			x2 = int((x_center + box_width / 2) * w)
			y2 = int((y_center + box_height / 2) * h)
			cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
			cv2.putText(image, str(int(cls)), (x1, y1 -10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
		return image

# Sort for consistent order
image_files = sorted([f for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".png", ".jpeg"))])

for filename in image_files:
	image_path = os.path.join(image_dir, filename)
	label_path = os.path.join(label_dir, filename.replace(".jpg", ".txt").replace(".png", ".txt"))
	
	img = cv2.imread(image_path)
	if img is None:
		print("Failed to load:", image_path)
		continue

	img_with_boxes = draw_yolo_boxes(img.copy(), label_path)
	cv2.imshow("Review Pseudo Labels", img_with_boxes)

	print(f"Reviewing {filename} -- Press k to KEEP, d to DISCARD, or q to quit.")

	while True:
		key = cv2.waitKey(0)
		if key == ord('q'): #ESC
			print("Exit requested")
			exit()
		elif key == ord('d'): # discard
			print(f"Discarded {filename}")
			shutil.move(image_path, os.path.join(discard_image_dir, filename))
			if os.path.exists(label_path):
				shutil.move(label_path, os.path.join(discard_label_dir, os.path.basename(label_path)))
			break
		elif key == ord('k'): # Keep
			print(f"Kept {filename}")
			shutil.move(image_path, os.path.join(verified_image_dir, filename))
			if os.path.exists(label_path):
				shutil.move(label_path, os.path.join(verified_label_dir, os.path.basename(label_path)))
			break

cv2.destroyAllWindows()