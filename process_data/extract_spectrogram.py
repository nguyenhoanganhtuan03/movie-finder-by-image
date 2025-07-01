import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import moviepy as mp
import json
from pathlib import Path

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def extract_wav_from_mp4(mp4_path, wav_path):
    clip = mp.VideoFileClip(mp4_path)
    if clip.audio is None:
        print(f"[WARNING] No audio track found in {mp4_path}")
        return
    clip.audio.write_audiofile(wav_path)
def generate_spectrogram(y, sr, save_path):
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    S_dB = librosa.power_to_db(S, ref=np.max)

    plt.figure(figsize=(2.24, 2.24), dpi=100)  # tạo ảnh ~224x224
    librosa.display.specshow(S_dB, sr=sr, x_axis=None, y_axis=None)
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
    plt.close()

def process_video_folder(main_folder, output_spectrogram_folder, metadata_output):
    metadata = []

    for movie_dir in os.listdir(main_folder):
        movie_path = os.path.join(main_folder, movie_dir)
        if not os.path.isdir(movie_path):
            continue

        # Tìm file mp4 trong thư mục phim
        mp4_files = [f for f in os.listdir(movie_path) if f.endswith('.mp4')]
        if not mp4_files:
            print(f"No MP4 found in {movie_path}")
            continue

        movie_spec_dir = os.path.join(output_spectrogram_folder, movie_dir)
        ensure_dir(movie_spec_dir)
        mp4_path = os.path.join(movie_path, mp4_files[0])
        wav_path = os.path.join(movie_spec_dir, "audio.wav")

        print(f"[INFO] Processing movie: {movie_dir}")
        extract_wav_from_mp4(mp4_path, wav_path)

        y, sr = librosa.load(wav_path, sr=22050)
        os.remove(wav_path)

        total_duration = librosa.get_duration(y=y, sr=sr)
        segment_len = 10  # giây
        n_segments = int(np.floor(total_duration / segment_len))

        for i in range(n_segments):
            start = i * segment_len
            end = start + segment_len
            y_seg = y[int(start * sr): int(end * sr)]

            spec_filename = f"{movie_dir}_{start:05d}_{end:05d}.png"
            spec_path = os.path.join(movie_spec_dir, spec_filename)
            generate_spectrogram(y_seg, sr, spec_path)

            metadata.append({
                "movie": movie_dir,
                "start_sec": start,
                "end_sec": end,
                "spectrogram_path": os.path.relpath(spec_path, start=output_spectrogram_folder)
            })

    # Ghi metadata thành file JSON
    with open(metadata_output, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"[DONE] Processed all movies. Metadata saved to {metadata_output}")

# === Thay đổi đường dẫn phù hợp ===
input_movies_folder = "E:\\Data\\Movie_Dataset\\Film_Dataset"
output_spectrogram_folder = "E:\\Data\\Movie_Dataset\\Spectrogram_Dataset"
metadata_output_file = "spectrogram_metadata.json"

# === Chạy pipeline ===
process_video_folder(input_movies_folder, output_spectrogram_folder, metadata_output_file)
