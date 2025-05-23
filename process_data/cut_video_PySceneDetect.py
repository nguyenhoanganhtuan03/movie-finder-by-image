import os
import shutil

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg
import unicodedata

# Hàm chuyển đổi tên file thành tên an toàn
def safe_folder_name(name):
    # Chuẩn hóa chuỗi và loại bỏ dấu
    normalized = unicodedata.normalize('NFD', name)
    no_accent = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')

    # Thay thế chữ Đ thành D
    no_d = no_accent.replace('Đ', 'D').replace('đ', 'd')

    # Loại bỏ ký tự đặc biệt, chỉ giữ lại chữ cái, số và dấu gạch dưới
    safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in no_d)
    return safe_name

def cut_video_with_pyscenedetect(video_path, output_dir, output_file_template, threshold=30.0, min_scene_length=15):
    os.makedirs(output_dir, exist_ok=True)

    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_length))

    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    scene_list = scene_manager.get_scene_list()
    print(f"[INFO] {len(scene_list)} cảnh được phát hiện trong {os.path.basename(video_path)}.")

    if len(scene_list) == 0:
        print("⚠️ Không phát hiện cảnh nào.")
        return 0

    split_video_ffmpeg(
        video_path,
        scene_list,
        # output_file_template=os.path.join(output_dir, "scene_$SCENE_NUMBER.mp4")
        output_file_template=output_file_template
    )

    video_manager.release()
    return len(scene_list)


def copy_all_posters(input_folder, output_folder):
    """Copy tất cả file ảnh poster từ thư mục input sang output với tên đã chuẩn hóa"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']

    for file in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file)
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in image_extensions:
                # Tạo tên an toàn từ tên gốc (không bao gồm phần mở rộng)
                filename_no_ext = os.path.splitext(file)[0]
                safe_name = safe_folder_name(filename_no_ext) + file_ext

                dst_path = os.path.join(output_folder, safe_name)
                try:
                    shutil.copy2(file_path, dst_path)
                    print(f"[POSTER] Đã copy ảnh: {file} -> {dst_path}")
                except Exception as e:
                    print(f"❌ Lỗi khi copy ảnh {file}: {e}")


def process_folder_structure_with_scenedetect(input_root, output_root, threshold=30.0, min_scene_length=15):
    for subfolder in os.listdir(input_root):
        n = 0

        sub_path = os.path.join(input_root, subfolder)
        if not os.path.isdir(sub_path):
            continue

        out_subdir = os.path.join(output_root, subfolder)
        os.makedirs(out_subdir, exist_ok=True)

        # Copy tất cả poster/ảnh trước
        print(f"📁 Đang xử lý thư mục: {subfolder}")
        copy_all_posters(sub_path, out_subdir)

        # Tìm và xử lý video
        mp4_files = [f for f in os.listdir(sub_path) if f.lower().endswith(".mp4")]
        if not mp4_files:
            print(f"[Bỏ qua] Không có file .mp4 trong: {sub_path}")
            continue

        for mp4_file in mp4_files:
            video_path = os.path.join(sub_path, mp4_file)

            print(f"🎬 Đang xử lý video: {video_path}")

            # Cắt video thành các cảnh với tên file gốc
            scene_template = os.path.join(out_subdir, f"{n}_scene_$SCENE_NUMBER.mp4")

            scene_count = cut_video_with_pyscenedetect(video_path, out_subdir, scene_template, threshold, min_scene_length)
            print(f"✅ Đã tách {scene_count} cảnh từ {mp4_file}\n")

            n = n + 1

        print(f"🏁 Hoàn thành xử lý thư mục: {subfolder}\n" + "=" * 50)


# Đường dẫn
input_video_path = 'E:\\Data\\Movie_Dataset\\Film_Dataset'
output_video_path = 'E:\\Data\\Movie_Dataset\\Film_Cut_Dataset'

# Gọi hàm chính
process_folder_structure_with_scenedetect(input_video_path, output_video_path, threshold=60.0, min_scene_length=20)