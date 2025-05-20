import os
import cv2
import random
import unicodedata

# Chuyển tên thư mục sang không dấu và không có ký tự đặc biệt (chỉ dùng khi lưu ảnh)
def safe_folder_name(name):
    normalized = unicodedata.normalize('NFD', name)
    no_accent = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in no_accent)
    return safe_name

# Tách và lưu frame từ video vào thư mục train/test
def extract_frames_from_video(video_path, train_dir, test_dir, target_size=(128, 128)):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Không mở được video: {video_path}")
        return

    # Lấy thông tin video
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps == 0:
        print(f"⚠️ FPS bằng 0: {video_path}")
        return

    duration = total_frames / fps
    print(f"[INFO] Đang xử lý: {video_path} | FPS: {fps:.2f}, Tổng frame: {total_frames}, Thời lượng: {duration:.2f}s")

    # Lấy tên thư mục của video
    video_folder = os.path.basename(os.path.dirname(video_path))

    # Xác định frame cần lấy
    if duration < 5:
        frames_to_extract = [total_frames // 2]
    elif duration < 10:
        frames_to_extract = [0, total_frames // 2, total_frames - 1]
    else:
        # Train/Test: 1: 7, 15   2: 20, 40
        # Test/Other: 1: 15, 30  2: 40, 80
        if video_folder.lower() == "khac":
            divisor = 40 if duration < 200 else 80
        else:
            divisor = 20 if duration < 200 else 40

        step = int(fps * (duration / divisor))
        step = max(step, 1)
        frames_to_extract = list(range(0, total_frames, step))

    frames_to_extract = set(int(i) for i in frames_to_extract)

    frames_not_needed = []
    frames_needed = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        try:
            resized = cv2.resize(frame, target_size)
        except Exception as e:
            print(f"❌ Resize lỗi tại frame {frame_idx}: {e}")
            frame_idx += 1
            continue

        if frame_idx in frames_to_extract:
            frames_needed.append((frame_idx, resized))
        else:
            frames_not_needed.append((frame_idx, resized))
        frame_idx += 1

    # Lưu frame
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    safe_folder = safe_folder_name(video_folder)

    # Lưu các frame cần thiết vào thư mục train
    for idx, frame in frames_needed:
        save_subdir = os.path.join(train_dir, safe_folder)
        os.makedirs(save_subdir, exist_ok=True)
        save_path = os.path.join(save_subdir, f"{video_name}_f{idx}.jpg")
        try:
            success = cv2.imwrite(save_path, frame)
            if not success:
                print(f"❌ Không thể lưu ảnh tại: {save_path}")
        except Exception as e:
            print(f"❌ Lỗi khi lưu ảnh: {e}")

    # Lưu các frame test được chọn ngẫu nhiên
    if frames_not_needed and frames_needed:
        num_frames_to_save = int(len(frames_needed) * 0.2)
        num_frames_to_save = max(1, num_frames_to_save)
        selected_frames = random.sample(frames_not_needed, min(num_frames_to_save, len(frames_not_needed)))

        for idx, frame in selected_frames:
            save_subdir = os.path.join(test_dir, safe_folder)
            os.makedirs(save_subdir, exist_ok=True)
            save_path = os.path.join(save_subdir, f"{video_name}_f{idx}.jpg")
            try:
                success = cv2.imwrite(save_path, frame)
                if not success:
                    print(f"❌ Không thể lưu test ảnh tại: {save_path}")
            except Exception as e:
                print(f"❌ Lỗi khi lưu test ảnh: {e}")

    cap.release()
    print(f"✅ Đã xử lý xong video: {video_path}\n")

# Xử lý toàn bộ thư mục chứa video
def process_all_videos(input_root, train_dir, test_dir):
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    for root, dirs, files in os.walk(input_root):
        for file in files:
            if file.lower().endswith((".mp4")):
                video_path = os.path.join(root, file)
                extract_frames_from_video(video_path, train_dir, test_dir)

# Cấu hình đường dẫn dữ liệu
input_folder = 'E:\\Data\\Film_Cut_Dataset'
frames_train = 'E:\\Data\\Extract_Frame_New_2\\Train'
frames_test = 'E:\\Data\\Extract_Frame_New_2\\Test'

# Gọi hàm chính để xử lý
process_all_videos(input_folder, frames_train, frames_test)
