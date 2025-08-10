import os
import numpy as np

# Định nghĩa các đuôi mở rộng của file video phổ biến
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}

def is_video_file(filename):
    return any(filename.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)

def count_videos_in_folder(root_dir):
    folder_counts = {}

    # Duyệt qua các thư mục con
    for subdir in os.listdir(root_dir):

        # if subdir.lower() == 'khac':
        #     continue

        subdir_path = os.path.join(root_dir, subdir)
        if os.path.isdir(subdir_path):
            video_count = 0
            for root, _, files in os.walk(subdir_path):
                video_count += sum(1 for f in files if is_video_file(f))
            folder_counts[subdir] = video_count

    return folder_counts

def summarize_counts(counts_dict):
    counts = list(counts_dict.values())
    total = sum(counts)
    mean = np.mean(counts)
    variance = np.var(counts)
    std_dev = np.std(counts)
    return total, mean, variance, std_dev

# ======== SỬ DỤNG ========
root_directory = "E:\\Data\\Movie_Dataset\\Film_Cut_Dataset_2"

video_counts = count_videos_in_folder(root_directory)

# In số lượng từng thư mục
print("Số lượng video trong từng thư mục con:")
for folder, count in video_counts.items():
    print(f"- {folder}: {count} video")

# Tính thống kê
total, mean, variance, std_dev = summarize_counts(video_counts)

# Tìm thư mục nhiều và ít video nhất
max_folder = max(video_counts, key=video_counts.get)
min_folder = min(video_counts, key=video_counts.get)

# In kết quả thống kê
print(f"\nTổng số video: {total}")
print(f"Trung bình mỗi thư mục: {mean:.2f}")
print(f"Phương sai số lượng video: {variance:.2f}")
print(f"Độ lệch chuẩn: {std_dev:.2f}")
print(f"Thư mục nhiều video nhất: {max_folder} ({video_counts[max_folder]} video)")
print(f"Thư mục ít video nhất: {min_folder} ({video_counts[min_folder]} video)")
