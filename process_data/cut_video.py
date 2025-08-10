import os
import cv2
import numpy as np
import csv
import shutil
import unicodedata
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# ==== Tạo tên thư mục an toàn ====
def safe_folder_name(name):
    normalized = unicodedata.normalize('NFD', name)
    no_accent = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    no_d = no_accent.replace('Đ', 'D').replace('đ', 'd')
    return ''.join(c if c.isalnum() or c == '_' else '_' for c in no_d)

# ==== Copy ảnh từ thư mục con qua output ====
def copy_images(src_dir, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    for file in os.listdir(src_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            src_file = os.path.join(src_dir, file)
            base, ext = os.path.splitext(file)
            safe_name = safe_folder_name(base) + ext.lower()
            dst_file = os.path.join(dst_dir, safe_name)
            shutil.copy2(src_file, dst_file)

# ==== Lấy thông tin video ====
def get_video_info(video_path):
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate',
        '-of', 'json',
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    info = json.loads(result.stdout)
    stream = info['streams'][0]
    fps_parts = stream['r_frame_rate'].split('/')
    fps = float(fps_parts[0]) / float(fps_parts[1])
    return int(fps), int(stream['width']), int(stream['height'])

# ==== Tính mức thay đổi pixel giữa 2 frame ====
def calculate_pixel_change(prev_frame, curr_frame):
    kernel = np.ones((3, 3), np.float32) / 9
    prev_blur = cv2.filter2D(prev_frame, -1, kernel)
    curr_blur = cv2.filter2D(curr_frame, -1, kernel)
    diff = cv2.absdiff(prev_blur, curr_blur)
    return np.mean(diff)

# ==== Đọc frame màu + gray từ ffmpeg ====
def read_frames_with_ffmpeg_both(video_path, width, height):
    cmd = [
        'ffmpeg', '-i', video_path,
        '-f', 'image2pipe',
        '-pix_fmt', 'rgb24',
        '-vcodec', 'rawvideo', '-'
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    frame_size_rgb = width * height * 3

    while True:
        raw_frame = proc.stdout.read(frame_size_rgb)
        if len(raw_frame) != frame_size_rgb:
            break
        frame_rgb = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
        frame_gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        yield frame_rgb, frame_gray

    proc.stdout.close()
    proc.wait()

# ==== Mở process ffmpeg để ghi video segment (màu gốc) ====
def open_ffmpeg_writer_color(filename, width, height, fps, ffmpeg_threads=2):
    return subprocess.Popen([
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-pix_fmt', 'rgb24',
        '-s', f'{width}x{height}',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-threads', str(ffmpeg_threads),
        filename
    ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

# ==== Cắt video nhưng tính change trên gray, ghi video màu ====
def cut_video_by_image_change(video_path, output_dir, log_list, seg_idx, movie_name,
                              change_threshold=20, min_segment_length=20):
    fps, width, height = get_video_info(video_path)
    video_name = os.path.basename(video_path)

    frames_iter = read_frames_with_ffmpeg_both(video_path, width, height)
    try:
        prev_rgb, prev_gray = next(frames_iter)
    except StopIteration:
        return seg_idx

    os.makedirs(output_dir, exist_ok=True)
    proc = open_ffmpeg_writer_color(os.path.join(output_dir, f"segment_{seg_idx:04}.mp4"), width, height, fps)

    frame_count = 1
    start_idx = 0
    current_idx = 1
    proc.stdin.write(prev_rgb.tobytes())

    for rgb_frame, gray_frame in frames_iter:
        pixel_change = calculate_pixel_change(prev_gray, gray_frame)

        if pixel_change > change_threshold and frame_count >= min_segment_length:
            proc.stdin.close()
            proc.wait()

            duration = frame_count / fps
            start_time = start_idx / fps
            log_list.append((movie_name, video_name, seg_idx, start_time, duration, start_idx, current_idx - 1))
            seg_idx += 1

            proc = open_ffmpeg_writer_color(os.path.join(output_dir, f"segment_{seg_idx:04}.mp4"), width, height, fps)
            start_idx = current_idx
            frame_count = 0

        proc.stdin.write(rgb_frame.tobytes())
        prev_gray = gray_frame
        current_idx += 1
        frame_count += 1

    if frame_count >= min_segment_length:
        proc.stdin.close()
        proc.wait()
        duration = frame_count / fps
        start_time = start_idx / fps
        log_list.append((movie_name, video_name, seg_idx, start_time, duration, start_idx, current_idx - 1))

    return seg_idx

# ==== Xử lý 1 video ====
def process_video_file(movie_folder, movie_path, mp4_file, movie_output_dir, change_threshold, min_segment_length):
    log_entries = []
    seg_idx = 1
    video_path = os.path.join(movie_path, mp4_file)
    seg_idx = cut_video_by_image_change(
        video_path, movie_output_dir, log_entries, seg_idx, safe_folder_name(movie_folder),
        change_threshold=change_threshold,
        min_segment_length=min_segment_length
    )
    return log_entries

# ==== Xử lý toàn bộ folder ====
def process_folder_structure(input_root, output_root, log_csv_path,
                             change_threshold=20, min_segment_length=20, max_workers=8):
    all_logs = []
    futures = []
    folder_futures = defaultdict(list)  # Map thư mục -> list future

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for movie_folder in os.listdir(input_root):
            movie_path = os.path.join(input_root, movie_folder)
            if not os.path.isdir(movie_path):
                continue
            if safe_folder_name(movie_folder).lower() == "khac":
                print(f"⏭ Bỏ qua thư mục: {movie_folder}")
                continue

            print(f"🚀 Bắt đầu xử lý thư mục: {movie_folder}")
            safe_name = safe_folder_name(movie_folder)
            movie_output_dir = os.path.join(output_root, safe_name)
            os.makedirs(movie_output_dir, exist_ok=True)

            copy_images(movie_path, movie_output_dir)
            mp4_files = [f for f in os.listdir(movie_path) if f.lower().endswith(".mp4")]

            for mp4_file in mp4_files:
                future = executor.submit(
                    process_video_file,
                    movie_folder, movie_path, mp4_file, movie_output_dir,
                    change_threshold, min_segment_length
                )
                futures.append(future)
                folder_futures[movie_folder].append(future)

        # Chờ tất cả video xong
        done_folders = set()
        for future in as_completed(futures):
            try:
                result = future.result()
                all_logs.extend(result)
            except Exception as e:
                print(f"❌ Lỗi khi xử lý video: {e}")

            # Kiểm tra thư mục nào đã hoàn thành tất cả video
            for folder, f_list in folder_futures.items():
                if folder not in done_folders and all(f.done() for f in f_list):
                    print(f"✅ Hoàn thành thư mục: {folder}")
                    done_folders.add(folder)

    # Lưu log CSV
    with open(log_csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=["movie", "video", "segment_id", "start_time", "duration", "frame_start", "frame_end"])
        csv_writer.writeheader()
        for movie, video, seg_id, start_t, dur, f_start, f_end in all_logs:
            csv_writer.writerow({
                'movie': movie,
                'video': video,
                'segment_id': seg_id,
                'start_time': f"{start_t:.2f}",
                'duration': f"{dur:.2f}",
                'frame_start': f_start,
                'frame_end': f_end
            })

# ==== Chạy ====
if __name__ == "__main__":
    input_video_path = r'E:\Data\Movie_Dataset\Film_Dataset'
    output_video_path = r'E:\Data\Movie_Dataset\Film_Cut_Dataset_2'
    log_csv_path = r'E:\Data\Movie_Dataset\Film_Cut_Dataset_2\segment_log.csv'

    process_folder_structure(
        input_video_path,
        output_video_path,
        log_csv_path,
        change_threshold=45,
        min_segment_length=30,
        max_workers=2
    )
