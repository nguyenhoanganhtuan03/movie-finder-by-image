import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import moviepy as mp
import json
from pathlib import Path
import random

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def extract_wav_from_mp4(mp4_path, wav_path):
    clip = mp.VideoFileClip(mp4_path)
    if clip.audio is None:
        print(f"[WARNING] No audio track found in {mp4_path}")
        return
    clip.audio.write_audiofile(wav_path, logger=None)

def generate_spectrogram(y, sr, save_path):
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    S_dB = librosa.power_to_db(S, ref=np.max)

    plt.figure(figsize=(2.24, 2.24), dpi=100)
    librosa.display.specshow(S_dB, sr=sr, x_axis=None, y_axis=None)
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
    plt.close()

def process_video_folder(main_folder, output_base_folder, metadata_output_dir):
    train_metadata = []
    test_metadata = []

    for movie_dir in os.listdir(main_folder):
        movie_path = os.path.join(main_folder, movie_dir)
        if not os.path.isdir(movie_path):
            continue

        mp4_files = [f for f in os.listdir(movie_path) if f.endswith('.mp4')]
        if not mp4_files:
            print(f"No MP4 found in {movie_path}")
            continue

        print(f"[INFO] Processing movie folder: {movie_dir}")

        for mp4_file in mp4_files:
            video_name = Path(mp4_file).stem
            mp4_path = os.path.join(movie_path, mp4_file)

            temp_dir = os.path.join(output_base_folder, "__temp_audio__")
            ensure_dir(temp_dir)
            wav_path = os.path.join(temp_dir, f"{video_name}_audio.wav")
            extract_wav_from_mp4(mp4_path, wav_path)

            if not os.path.exists(wav_path):
                continue

            y, sr = librosa.load(wav_path, sr=22050)
            os.remove(wav_path)

            total_duration = librosa.get_duration(y=y, sr=sr)
            segment_len = 10
            n_segments = int(np.floor(total_duration / segment_len))

            used_segments = set()
            for i in range(n_segments):
                start = i * segment_len
                end = start + segment_len
                y_seg = y[int(start * sr): int(end * sr)]

                save_dir = os.path.join(output_base_folder, 'Train', movie_dir)
                ensure_dir(save_dir)
                spec_filename = f"{video_name}_{start:05d}_{end:05d}.png"
                spec_path = os.path.join(save_dir, spec_filename)
                generate_spectrogram(y_seg, sr, spec_path)

                used_segments.add(i)
                train_metadata.append({
                    "type": "train",
                    "movie": movie_dir,
                    "video": video_name,
                    "start_sec": start,
                    "end_sec": end,
                    "spectrogram_path": os.path.relpath(spec_path, start=output_base_folder)
                })

            # === Sinh tập test từ các đoạn ngẫu nhiên (có thể trùng với đoạn Train)
            n_test = int(len(used_segments) * 0.3)
            test_start_times = set()
            max_attempts = 100 * n_test
            attempts = 0

            while len(test_start_times) < n_test and attempts < max_attempts:
                rand_start = random.uniform(0, total_duration - segment_len)
                rand_start_rounded = round(rand_start, 2)  # làm tròn 2 chữ số sau dấu phẩy để tránh trùng
                if rand_start_rounded not in test_start_times:
                    test_start_times.add(rand_start_rounded)
                attempts += 1

            for start in test_start_times:
                end = start + segment_len
                y_seg = y[int(start * sr): int(end * sr)]

                save_dir = os.path.join(output_base_folder, 'Test', movie_dir)
                ensure_dir(save_dir)
                spec_filename = f"{video_name}_{int(start):05d}_{int(end):05d}.png"
                spec_path = os.path.join(save_dir, spec_filename)
                generate_spectrogram(y_seg, sr, spec_path)

                test_metadata.append({
                    "type": "test",
                    "movie": movie_dir,
                    "video": video_name,
                    "start_sec": round(start, 2),
                    "end_sec": round(end, 2),
                    "spectrogram_path": os.path.relpath(spec_path, start=output_base_folder)
                })

    # Ghi metadata ra file
    ensure_dir(metadata_output_dir)
    with open(os.path.join(metadata_output_dir, 'spectrogram_metadata_train.json'), 'w', encoding='utf-8') as f:
        json.dump(train_metadata, f, indent=2, ensure_ascii=False)

    with open(os.path.join(metadata_output_dir, 'spectrogram_metadata_test.json'), 'w', encoding='utf-8') as f:
        json.dump(test_metadata, f, indent=2, ensure_ascii=False)

    print(f"[DONE] Generated {len(train_metadata)} train and {len(test_metadata)} test spectrograms.")

# === Đường dẫn đầu vào và đầu ra ===
input_movies_folder = "E:\\Data\\Movie_Dataset\\Film_Dataset"
output_spectrogram_folder = "E:\\Data\\Movie_Dataset\\Spectrogram_Dataset"  # cha chứa train/ và test/
metadata_output_dir = output_spectrogram_folder  # lưu JSON vào đây

process_video_folder(input_movies_folder, output_spectrogram_folder, metadata_output_dir)
