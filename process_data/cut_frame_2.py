import os
import cv2
import random
import unicodedata


# === Hàm chuẩn hóa tên thư mục & file ===
def safe_folder_name(name):
    normalized = unicodedata.normalize('NFD', name)
    no_accent = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    no_d = no_accent.replace('Đ', 'D').replace('đ', 'd')
    safe_name = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in no_d)
    return '_'.join(safe_name.split())


# === Lấy frame từ video ===
def extract_frames(video_path, frames_needed_idx, target_size=(224, 224)):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Không mở được video: {video_path}")
        return []
    frames = []
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx in frames_needed_idx:
            try:
                resized = cv2.resize(frame, target_size)
                frames.append((frame_idx, resized))
            except:
                pass
        frame_idx += 1
    cap.release()
    return frames


# === Xác định frame cho Train từ video ngắn ===
def get_train_frame_idx(total_frames, duration):
    if duration < 5:
        return {total_frames // 2}
    elif duration < 10:
        return {total_frames // 2, total_frames - 1}
    elif duration < 30:
        num_samples = 5
    elif duration < 180:
        num_samples = 10
    else:
        num_samples = 20
    return {int(i * total_frames / num_samples) for i in range(num_samples)}


# === Xử lý Train từ tất cả video ngắn trong thư mục con ===
import shutil

def process_train_videos(input_subfolder, train_dir, label_folder, target_size=(224, 224)):
    """Xử lý tất cả video ngắn trong một thư mục con để lấy frame train và copy ảnh đầu tiên nếu có"""
    safe_label = safe_folder_name(label_folder)
    train_subdir = os.path.join(train_dir, safe_label)
    os.makedirs(train_subdir, exist_ok=True)

    total_train_frames = 0
    first_image_copied = False  # Đảm bảo chỉ copy 1 ảnh đầu tiên

    # Duyệt qua tất cả file trong thư mục con
    for root, dirs, files in os.walk(input_subfolder):
        # Copy ảnh đầu tiên nếu có
        if not first_image_copied:
            img_files = [f for f in files if f.lower().endswith(('.jpg', '.png'))]
            if img_files:
                src_img_path = os.path.join(root, img_files[0])
                dst_img_path = os.path.join(train_subdir, safe_folder_name(os.path.splitext(img_files[0])[0]) + os.path.splitext(img_files[0])[1])
                shutil.copy2(src_img_path, dst_img_path)
                first_image_copied = True

        # Lấy video để xử lý
        mp4_files = [f for f in files if f.lower().endswith(".mp4")]

        for mp4_file in mp4_files:
            video_path = os.path.join(root, mp4_file)

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"❌ Không mở được video: {video_path}")
                continue

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()

            if fps <= 0 or total_frames <= 0:
                continue

            duration = total_frames / fps
            video_name = os.path.splitext(mp4_file)[0]

            # Xác định frame cần lấy
            frames_needed_idx = get_train_frame_idx(total_frames, duration)

            # Lấy và lưu frames
            frames = extract_frames(video_path, frames_needed_idx, target_size)
            for idx, frame in frames:
                save_path = os.path.join(train_subdir, f"{safe_folder_name(video_name)}_f{idx}.jpg")
                cv2.imwrite(save_path, frame)
                total_train_frames += 1

    return total_train_frames


# === Tìm video gốc từ thư mục root ===
def find_original_video(root_folder, label_folder):
    """Tìm video gốc trong thư mục root dựa trên tên thư mục con"""
    label_path = os.path.join(root_folder, label_folder)
    if not os.path.exists(label_path):
        return None

    for root, dirs, files in os.walk(label_path):
        mp4_files = [f for f in files if f.lower().endswith(".mp4")]
        if mp4_files:
            return os.path.join(root, mp4_files[0])  # Trả về đường dẫn file mp4 đầu tiên
    return None


# === Xử lý Test từ video gốc ===
def process_test_video(original_video_path, test_dir, label_folder, train_count, target_size=(224, 224)):
    """
    Xử lý video gốc để lấy frame test ngẫu nhiên, trải đều trên toàn bộ video
    - Nhận trực tiếp đường dẫn file mp4
    """
    if not original_video_path or not os.path.exists(original_video_path):
        print(f"❌ Không tìm thấy video gốc cho {label_folder}")
        return 0

    cap = cv2.VideoCapture(original_video_path)
    if not cap.isOpened():
        print(f"❌ Không mở được video gốc: {original_video_path}")
        return 0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    # Tính số frame test cần lấy (30% của train)
    test_count = max(1, int(train_count * 0.3))

    # Chọn frame ngẫu nhiên nhưng trải đều
    if total_frames <= test_count:
        selected_test_idx = list(range(total_frames))
    else:
        segment_len = total_frames / test_count
        selected_test_idx = []
        for i in range(test_count):
            start = int(i * segment_len)
            end = int((i + 1) * segment_len)
            if end > total_frames:
                end = total_frames
            if start >= end:
                start = max(0, end - 1)
            selected_test_idx.append(random.randint(start, end - 1))

    # Lấy frames
    test_frames = extract_frames(original_video_path, selected_test_idx, target_size)

    # Lưu Test frames
    safe_label = safe_folder_name(label_folder)
    test_subdir = os.path.join(test_dir, safe_label)
    os.makedirs(test_subdir, exist_ok=True)

    video_name = os.path.splitext(os.path.basename(original_video_path))[0]
    for idx, frame in test_frames:
        save_path = os.path.join(test_subdir, f"{safe_folder_name(video_name)}_original_f{idx}.jpg")
        cv2.imwrite(save_path, frame)

    return len(test_frames)


# === Xử lý tất cả video ===
def process_all_videos(input_root, root_folder, train_dir, test_dir, target_size=(224, 224)):
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    # Duyệt qua các thư mục con trong input_root
    for item in os.listdir(input_root):
        item_path = os.path.join(input_root, item)
        if not os.path.isdir(item_path):
            continue

        label_folder = item  # Tên thư mục con chính là label
        print(f"\n🎬 Đang xử lý: {label_folder}")

        # Train - từ tất cả video ngắn trong thư mục con
        train_count = process_train_videos(item_path, train_dir, label_folder, target_size)

        if train_count == 0:
            print(f"❌ Không có frame train nào được tạo cho {label_folder}")
            continue

        # Test - từ video gốc trong thư mục root
        original_video_path = find_original_video(root_folder, safe_folder_name(label_folder))
        test_count = process_test_video(original_video_path, test_dir, label_folder, train_count, target_size)

        print(f"✅ {label_folder}:")
        print(f"   Train (từ các video ngắn): {train_count} ảnh")
        print(f"   Test (từ video gốc): {test_count} ảnh")
        print(f"   Video gốc: {original_video_path}")


# === Config ===
root_folder = r'E:\Data\Movie_Dataset\Film_Dataset'
input_folder = r'E:\Data\Movie_Dataset\Film_Cut_Dataset_2'
frames_train = r'E:\Data\Movie_Dataset\Extract_Frames_2\Train'
frames_test = r'E:\Data\Movie_Dataset\Extract_Frames_2\Test'

process_all_videos(input_folder, root_folder, frames_train, frames_test)