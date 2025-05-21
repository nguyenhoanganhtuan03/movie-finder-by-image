import os
import cv2
import numpy as np
import shutil

def is_dominated_by_one_color(image_path, threshold=0.9):
    img = cv2.imread(image_path)
    if img is None:
        return True  # ảnh lỗi => bỏ qua

    # Resize nhỏ lại để tăng tốc xử lý
    img_resized = cv2.resize(img, (128, 128))
    pixels = img_resized.reshape(-1, 3)

    # Làm tròn giá trị màu để giảm số lượng màu cần phân biệt
    rounded_pixels = (pixels // 10) * 10  # làm tròn bớt để gom nhóm màu tương tự

    # Đếm số pixel theo từng màu
    unique_colors, counts = np.unique(rounded_pixels, axis=0, return_counts=True)

    # Tính tỷ lệ cao nhất
    max_ratio = np.max(counts) / len(pixels)

    return max_ratio >= threshold

def copy_valid_images(input_root, output_root, threshold=0.9):
    for label_name in os.listdir(input_root):
        label_path = os.path.join(input_root, label_name)
        if not os.path.isdir(label_path):
            continue

        output_label_path = os.path.join(output_root, label_name)
        os.makedirs(output_label_path, exist_ok=True)

        for file_name in os.listdir(label_path):
            file_path = os.path.join(label_path, file_name)
            if not os.path.isfile(file_path):
                continue

            try:
                if not is_dominated_by_one_color(file_path, threshold):
                    shutil.copy2(file_path, os.path.join(output_label_path, file_name))
                    print(f"Copied: {file_path}")
                else:
                    print(f"Skipped (single color): {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

# Sử dụng:
input_root = "E:\\Data\\Extract_Frame_New_2\\Test"
output_root = "E:\\Data\\Process_Frame_2\\Test"
copy_valid_images(input_root, output_root)
