import os
import cv2
import numpy as np
import csv
import shutil
import unicodedata
import subprocess
from concurrent.futures import as_completed
from concurrent.futures import ProcessPoolExecutor
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


# ==== Tính mức thay đổi pixel giữa 2 frame ====
def calculate_pixel_change(prev_frame, curr_frame):
    prev_blur = cv2.GaussianBlur(prev_frame, (3, 3), 0)
    curr_blur = cv2.GaussianBlur(curr_frame, (3, 3), 0)
    diff = np.abs(prev_blur.astype(np.int16) - curr_blur.astype(np.int16))
    return diff.mean()

# ==== Phân tích video để tìm cut points ====
def analyze_video_cuts(video_path, change_threshold=20, min_segment_length=20):
    """Chỉ phân tích video để tìm điểm cắt, không tạo file"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        prev_gray_small = None
        cut_points = [0]  # Bắt đầu từ frame 0
        frame_count = 0
        current_frame = 0

        print(f"  🔍 Phân tích video: {total_frames} frames, {fps:.1f} FPS")

        # Sample frames để tăng tốc (không cần xử lý mọi frame)
        frame_skip = int(fps)

        while current_frame < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret:
                break

            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_gray_small = cv2.resize(frame_gray, (32, 32))

            if prev_gray_small is not None:
                pixel_change = calculate_pixel_change(prev_gray_small, frame_gray_small)

                if pixel_change > change_threshold and frame_count >= min_segment_length:
                    cut_points.append(current_frame)
                    frame_count = 0

            prev_gray_small = frame_gray_small
            frame_count += frame_skip
            current_frame += frame_skip

        # Thêm frame cuối
        if cut_points[-1] != total_frames:
            cut_points.append(total_frames)

        cap.release()

        # Convert thành time segments
        segments = []
        for i in range(len(cut_points) - 1):
            start_frame = cut_points[i]
            end_frame = cut_points[i + 1]

            if end_frame - start_frame >= min_segment_length:
                start_time = start_frame / fps
                end_time = end_frame / fps
                duration = end_time - start_time
                segments.append((start_time, end_time, duration, start_frame, end_frame))

        print(f"  ✂️ Tìm thấy {len(segments)} segments")
        return segments

    except Exception as e:
        print(f"❌ Lỗi phân tích video: {e}")
        return []


# ==== Cắt video bằng FFmpeg (siêu nhanh) ====
def cut_video_ffmpeg(video_path, segments, output_dir, movie_name, video_name):
    """Sử dụng FFmpeg để cắt video nhanh và nén tốt"""
    log_entries = []

    for i, (start_time, end_time, duration, start_frame, end_frame) in enumerate(segments, 1):
        segment_path = os.path.join(output_dir, f"segment_{i:04d}.mp4")

        cmd = [
            'ffmpeg', '-y',
            '-ss', f'{start_time:.3f}',
            '-i', video_path,
            '-t', f'{duration:.3f}',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-an',
            '-movflags', '+faststart',
            segment_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                file_size = os.path.getsize(segment_path) / (1024 * 1024)
                # print(f"  ✅ segment_{i:04d}.mp4 - {duration:.1f}s, {file_size:.1f}MB")

                log_entries.append((movie_name, video_name, i, start_time, duration, start_frame, end_frame))
            else:
                print(f"  ❌ Lỗi tạo segment_{i:04d}: {result.stderr}")

        except Exception as e:
            print(f"  ❌ Exception tạo segment_{i:04d}: {e}")

    return log_entries

# ==== Xử lý 1 video ====
def process_video_file(movie_folder, movie_path, mp4_file, movie_output_dir,
                       change_threshold, min_segment_length):
    log_entries = []
    video_path = os.path.join(movie_path, mp4_file)
    movie_name = safe_folder_name(movie_folder)

    print(f"🎬 Đang xử lý video: {mp4_file}")

    # Bước 1: Phân tích tìm cut points
    segments = analyze_video_cuts(video_path, change_threshold, min_segment_length)

    if not segments:
        print(f"  ⚠️ Không tìm thấy segments phù hợp")
        return log_entries

    # Bước 2: Cắt video
    print(f"  🚀 Sử dụng FFmpeg để cắt video")
    log_entries = cut_video_ffmpeg(video_path, segments, movie_output_dir, movie_name, mp4_file)

    return log_entries


# ==== Xử lý toàn bộ folder ====
def process_folder_structure(input_root, output_root, log_csv_path,
                             change_threshold=20, min_segment_length=20,
                             max_workers=2):

    all_logs = []
    futures = []
    folder_futures = defaultdict(list)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
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

        done_folders = set()
        for future in as_completed(futures):
            try:
                result = future.result()
                all_logs.extend(result)
            except Exception as e:
                print(f"❌ Lỗi khi xử lý video: {e}")

            for folder, f_list in folder_futures.items():
                if folder not in done_folders and all(f.done() for f in f_list):
                    print(f"✅ Hoàn thành thư mục: {folder}")
                    done_folders.add(folder)

    # Phần lưu log CSV và tính dung lượng giữ nguyên như bạn đã có

    print(f"💾 Đang lưu log vào: {log_csv_path}")
    with open(log_csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file,
                                    fieldnames=["movie", "video", "segment_id", "start_time", "duration",
                                                "frame_start", "frame_end"])
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

    total_segments = len(all_logs)
    print(f"🎉 Hoàn thành! Đã tạo {total_segments} segments")

    if total_segments > 0:
        total_size = 0
        for root, dirs, files in os.walk(output_root):
            for file in files:
                if file.endswith('.mp4'):
                    total_size += os.path.getsize(os.path.join(root, file))

        total_size_mb = total_size / (1024 * 1024)
        avg_size_mb = total_size_mb / total_segments
        print(f"📊 Tổng dung lượng: {total_size_mb:.1f}MB, trung bình: {avg_size_mb:.1f}MB/segment")


# ==== Chạy ====
if __name__ == "__main__":
    input_video_path = r'E:\Data\Movie_Dataset\Film_Dataset'
    output_video_path = r'E:\Data\Movie_Dataset\Film_Cut_Dataset_2'
    log_csv_path = r'E:\Data\Movie_Dataset\Film_Cut_Dataset_2\segment_log.csv'

    # Tạo thư mục output nếu chưa có
    os.makedirs(output_video_path, exist_ok=True)

    process_folder_structure(
        input_video_path,
        output_video_path,
        log_csv_path,
        change_threshold=45,
        min_segment_length=30,
        max_workers=4,
    )