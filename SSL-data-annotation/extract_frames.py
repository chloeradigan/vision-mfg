import cv2
import os

def extract_frames(video_path, output_folder, total_frames):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Load the video
    video_capture = cv2.VideoCapture(video_path)
    total_video_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))  # total frames
    fps = video_capture.get(cv2.CAP_PROP_FPS)  # Get frames per second
    duration = total_video_frames / fps  # duration in seconds

    if not video_capture.isOpened():
        print("Error: Could not open the video.")
        return

    print(f"Video Info: {total_video_frames} frames, {fps} fps, {duration:.2f} seconds")
    
    frame_interval = max(total_video_frames // total_frames, 1)  # Interval to capture frames
    print(f"Frame Interval: Capture every {frame_interval} frames.")

    print(f"Processing video: {video_path}")
    
    frame_count = 0
    extracted_count = 0

    while frame_count < total_video_frames:
        ret, frame = video_capture.read()
        if not ret:
            break  # Exit loop if no more frames are available.

        # Save frame if it matches the frame interval
        if frame_count % frame_interval == 0:
            output_path = os.path.join(output_folder, f"frame_{extracted_count:04d}.jpg")
            cv2.imwrite(output_path, frame)  # Save frame as an image
            extracted_count += 1

            if extracted_count >= total_frames:
                break

        frame_count += 1

    # Release video capture once done
    video_capture.release()
    
    print(f"Extraction completed. {extracted_count} frames saved in {output_folder}.")

# Parameters
video_file = "WIN_20250102_13_38_13_Pro.mp4"  # Path to video file
output_directory = "frames_output"  # Directory to save extracted images
total_images = 1500  # Adjust to extract desired images over video length

# Extract frames
extract_frames(video_file, output_directory, total_images)
