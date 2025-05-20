import os
import cv2
import numpy as np
import librosa
import soundfile as sf
import csv

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg

# ==== Các hàm xử lý đặc trưng ====
def calculate_frame_difference(prev_frame, curr_frame, threshold=5000):
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
    frame_diff = cv2.absdiff(prev_gray, curr_gray)
    return np.count_nonzero(frame_diff) > threshold

def average_color(frame):
    return np.mean(frame, axis=(0, 1))

def is_similar_color(c1, c2, threshold=30):
    return np.linalg.norm(c1 - c2) < threshold

def average_brightness(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)

# ==== Xử lý âm thanh ====
def extract_audio_ffmpeg(video_path, audio_path="temp_audio.wav"):
    os.system(f"ffmpeg -y -i \"{video_path}\" -vn -acodec pcm_s16le -ar 22050 -ac 1 \"{audio_path}\"")

def get_audio_rms_librosa(audio_path, frame_count, fps):
    y, sr = librosa.load(audio_path, sr=None)
    hop_length = int(sr / fps)
    rms = librosa.feature.rms(y=y, frame_length=hop_length * 2, hop_length=hop_length)[0]
    return rms[:frame_count]

def add_audio_to_video(video_path, original_audio, output_path, start_time, duration):
    temp_audio = "segment_audio.wav"
    os.system(f"ffmpeg -y -i \"{original_audio}\" -ss {start_time:.2f} -t {duration:.2f} -acodec copy \"{temp_audio}\"")
    os.system(f"ffmpeg -y -i \"{video_path}\" -i \"{temp_audio}\" -c:v copy -c:a aac -strict experimental \"{output_path}\"")
    os.remove(video_path)
    os.remove(temp_audio)

# ==== Ghi đoạn video ra file ====
def save_segment(output_dir, frames, fps, width, height, seg_idx):
    filename = os.path.join(output_dir, f"segment_{seg_idx:03}.avi")
    out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))
    for f in frames:
        out.write(f)
    out.release()
    return filename

# ==== Ghi log vào CSV ====
def write_log_csv(csv_writer, video_name, seg_idx, start_time, duration, frame_start, frame_end):
    csv_writer.writerow({
        'video': video_name,
        'segment_id': seg_idx,
        'start_time': f"{start_time:.2f}",
        'duration': f"{duration:.2f}",
        'frame_start': frame_start,
        'frame_end': frame_end
    })

# ==== Cắt video ====
def cut_video_by_features(video_path, output_dir, csv_writer, color_thresh, audio_thresh, min_segment_length, motion_thresh, brightness_thresh):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[Lỗi] Không mở được video: {video_path}")
        return 0

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_name = os.path.basename(video_path)

    audio_path = "temp_audio.wav"
    extract_audio_ffmpeg(video_path, audio_path)
    audio_rms = get_audio_rms_librosa(audio_path, total_frames, fps)

    os.makedirs(output_dir, exist_ok=True)
    seg_idx = 0

    ret, prev_frame = cap.read()
    if not ret:
        cap.release()
        os.remove(audio_path)
        return 0

    segment_frames = [prev_frame]
    prev_color = average_color(prev_frame)
    prev_audio = audio_rms[0]
    prev_brightness = average_brightness(prev_frame)
    start_idx = 0
    current_idx = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        curr_color = average_color(frame)
        curr_audio = audio_rms[current_idx] if current_idx < len(audio_rms) else 0
        curr_brightness = average_brightness(frame)

        color_changed = not is_similar_color(curr_color, prev_color, color_thresh)
        audio_changed = abs(curr_audio - prev_audio) > audio_thresh
        motion_detected = calculate_frame_difference(prev_frame, frame, motion_thresh)
        brightness_changed = abs(curr_brightness - prev_brightness) > brightness_thresh

        if color_changed and audio_changed and motion_detected and brightness_changed:
            if len(segment_frames) >= min_segment_length:
                segment_path = save_segment(output_dir, segment_frames, fps, width, height, seg_idx)
                duration = len(segment_frames) / fps
                start_time = start_idx / fps
                final_output = os.path.join(output_dir, f"segment_{seg_idx:03}_with_audio.mp4")
                add_audio_to_video(segment_path, audio_path, final_output, start_time, duration)
                write_log_csv(csv_writer, video_name, seg_idx, start_time, duration, start_idx, current_idx - 1)
                seg_idx += 1

            segment_frames = [frame]
            start_idx = current_idx
        else:
            segment_frames.append(frame)

        prev_frame = frame
        prev_color = curr_color
        prev_audio = curr_audio
        prev_brightness = curr_brightness
        current_idx += 1

    # Lưu đoạn cuối nếu còn lại
    if len(segment_frames) >= min_segment_length:
        segment_path = save_segment(output_dir, segment_frames, fps, width, height, seg_idx)
        duration = len(segment_frames) / fps
        start_time = start_idx / fps
        final_output = os.path.join(output_dir, f"segment_{seg_idx:03}_with_audio.mp4")
        add_audio_to_video(segment_path, audio_path, final_output, start_time, duration)
        write_log_csv(csv_writer, video_name, seg_idx, start_time, duration, start_idx, current_idx - 1)

    cap.release()
    os.remove(audio_path)
    return seg_idx + 1

# ==== Xử lý thư mục nhiều video ====
def process_folder_structure(input_root, output_root, log_csv_path, color_thresh, audio_thresh, min_segment_length, motion_thresh, brightness_thresh):
    with open(log_csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=["video", "segment_id", "start_time", "duration", "frame_start", "frame_end"])
        csv_writer.writeheader()

        for subfolder in os.listdir(input_root):
            sub_path = os.path.join(input_root, subfolder)
            if os.path.isdir(sub_path):
                mp4_files = [f for f in os.listdir(sub_path) if f.endswith(".mp4")]
                if not mp4_files:
                    print(f"[Bỏ qua] Không tìm thấy file .mp4 trong: {sub_path}")
                    continue

                video_path = os.path.join(sub_path, mp4_files[0])
                out_subdir = os.path.join(output_root, subfolder)
                print(f"🔍 Đang xử lý: {subfolder}")
                segment_count = cut_video_by_features(
                    video_path, out_subdir, csv_writer,
                    color_thresh, audio_thresh, min_segment_length, motion_thresh, brightness_thresh
                )
                print(f"✅ Đã xử lý {segment_count} đoạn trong {subfolder}\n")

# ==== Chạy chương trình chính ====
input_video_path = 'E:\\Data\\Film_Dataset'
output_video_path = 'E:\\Data\\Film_Cut_Dataset'
log_csv_path = 'segment_log.csv'

process_folder_structure(
    input_video_path,
    output_video_path,
    log_csv_path,
    color_thresh=60,
    audio_thresh=0.01,
    min_segment_length=20,
    motion_thresh=6000,
    brightness_thresh=5
)
