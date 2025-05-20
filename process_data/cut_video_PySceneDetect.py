import os
import cv2
import numpy as np
import librosa
import soundfile as sf
import csv

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg


# Hàm tách video bằng PySceneDetect và lưu vào thư mục tương ứng
def cut_video_with_pyscenedetect(video_path, output_dir, threshold=30.0, min_scene_length=15):
    # Tạo thư mục nếu chưa có
    os.makedirs(output_dir, exist_ok=True)

    # Tạo các đối tượng quản lý video và cảnh
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_length))

    # Khởi tạo xử lý video
    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    # Lấy danh sách các cảnh
    scene_list = scene_manager.get_scene_list()
    print(f"[INFO] {len(scene_list)} cảnh được phát hiện trong {os.path.basename(video_path)}.")

    if len(scene_list) == 0:
        print("⚠️ Không phát hiện cảnh nào.")
        return 0

    # Tách và lưu các cảnh thành file .mp4
    split_video_ffmpeg(
        video_path,
        scene_list,
        output_file_template=os.path.join(output_dir, "scene_$SCENE_NUMBER.mp4")
    )

    video_manager.release()
    return len(scene_list)


# Xử lý toàn bộ thư mục chứa video
def process_folder_structure_with_scenedetect(input_root, output_root, threshold=30.0, min_scene_length=15):
    for subfolder in os.listdir(input_root):  # Duyệt qua từng thư mục con trong input_root
        sub_path = os.path.join(input_root, subfolder)

        if os.path.isdir(sub_path):  # Chỉ xử lý thư mục
            # Tìm tất cả các file .mp4 trong thư mục con
            mp4_files = [f for f in os.listdir(sub_path) if f.endswith(".mp4")]
            if not mp4_files:
                print(f"[Bỏ qua] Không tìm thấy file .mp4 trong: {sub_path}")
                continue

            # Tạo thư mục đầu ra tương ứng với thư mục con trong input_root
            out_subdir = os.path.join(output_root, subfolder)
            os.makedirs(out_subdir, exist_ok=True)

            for mp4_file in mp4_files:
                video_path = os.path.join(sub_path, mp4_file)

                # Tạo thư mục riêng cho từng video nếu cần phân biệt
                video_name = os.path.splitext(mp4_file)[0]
                out_video_dir = os.path.join(out_subdir, video_name)
                os.makedirs(out_video_dir, exist_ok=True)

                print(f"🎬 Đang xử lý video: {video_path}")
                scene_count = cut_video_with_pyscenedetect(video_path, out_video_dir, threshold, min_scene_length)
                print(f"✅ Đã tách {scene_count} cảnh và lưu vào: {out_video_dir}\n")

# Đường dẫn vào/ra
input_video_path = 'E:\\Data\\Other_Film_Dataset'
output_video_path = 'E:\\Data\\Other_Film_Cut_Dataset'

# Gọi hàm chính
process_folder_structure_with_scenedetect(input_video_path, output_video_path, threshold=60.0, min_scene_length=20)