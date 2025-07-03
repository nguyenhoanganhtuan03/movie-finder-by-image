import os
import numpy as np

def count_images_per_folder(root_dir, image_extensions=None):
    if image_extensions is None:
        image_extensions = ['.jpg', '.png']

    folder_image_counts = {}  # Lưu số lượng ảnh theo thư mục
    total = 0

    for subdir, dirs, files in os.walk(root_dir):

        # folder_name = os.path.basename(subdir).lower()
        # if folder_name == 'khac':
        #     continue

        count = sum(1 for file in files if any(file.lower().endswith(ext) for ext in image_extensions))
        if count > 0:
            relative_path = os.path.relpath(subdir, root_dir)
            folder_image_counts[relative_path] = count
            print(f"Thư mục '{relative_path}': {count} ảnh")
            total += count

    # Tính thống kê nếu có dữ liệu
    if folder_image_counts:
        counts = list(folder_image_counts.values())
        mean = np.mean(counts)
        std_dev = np.std(counts)
        max_folder = max(folder_image_counts, key=folder_image_counts.get)
        min_folder = min(folder_image_counts, key=folder_image_counts.get)

        print(f"\n📊 Tổng số ảnh: {total}")
        print(f"📌 Trung bình mỗi thư mục: {mean:.2f} ảnh")
        print(f"📉 Độ lệch chuẩn: {std_dev:.2f} ảnh")
        print(f"📈 Thư mục nhiều ảnh nhất: '{max_folder}' ({folder_image_counts[max_folder]} ảnh)")
        print(f"📉 Thư mục ít ảnh nhất: '{min_folder}' ({folder_image_counts[min_folder]} ảnh)")
    else:
        print("⚠️ Không tìm thấy ảnh nào.")

# ======== SỬ DỤNG ========

print("==== Thư mục Train ====")
folder_train_path = 'E:\\Data\\Movie_Dataset\\Spectrogram_Dataset\\Train'
count_images_per_folder(folder_train_path)

print("\n==== Thư mục Test ====")
folder_test_path = 'E:\\Data\\Movie_Dataset\\Spectrogram_Dataset\\Test'
count_images_per_folder(folder_test_path)
