import os
import time
import numpy as np
import faiss
import cv2
import librosa
import soundfile as sf
import tempfile
import matplotlib.pyplot as plt
from PIL import Image
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from collections import Counter
from tensorflow.keras.applications.resnet50 import preprocess_input
from app.models.models_audio.call_model_cnn import call_model

# ==== Cấu hình ====
IMAGE_SIZE = 224
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "features_faiss/resnet50/faiss_features.index")
LABEL_PATH = os.path.join(BASE_DIR, "features_faiss/resnet50/faiss_labels.npy")

# SIMILARITY_THRESHOLD = 0.8
# TOP_K = 3

CLASSES = {
    1: "21 Ngày Yêu Em", 2: "4 Năm 2 Chàng 1 Tình Yêu", 3: "Ăn Tết Bên Cồn", 4: "Bẫy Ngọt Ngào", 5: "Bệnh Viện Ma",
    6: "Bí Mật Lại Bị Mất", 7: "Bí Mật Trong Sương Mù", 8: "Bộ Tứ Oan Gia", 9: "Chờ Em Đến Ngày Mai",
    10: "Chủ Tịch Giao Hàng", 11: "Chuyện Tết", 12: "Cô Ba Sài Gòn", 13: "Đào, Phở Và Piano", 14: "Đất Rừng Phương Nam",
    15: "Địa Đạo", 16: "Định Mệnh Thiên Ý", 17: "Đôi Mắt Âm Dương", 18: "Em Chưa 18", 19: "Em Là Của Em",
    20: "Gái Già Lắm Chiêu 3", 21: "Giả Nghèo Gặp Phật", 22: "Hẻm Cụt", 23: "Hoán Đổi", 24: "Kẻ Ẩn Danh",
    25: "Kẻ Ăn Hồn", 26: "Làm Giàu Với Ma", 27: "Lật Mặt 1", 28: "Lộ Mặt", 29: "Ma Da", 30: "Mắt Biếc",
    31: "Nghề Siêu Dễ", 32: "Những Nụ Hôn Rực Rỡ", 33: "Ông Ngoại Tuổi 30", 34: "Pháp Sư Tập Sự", 35: "Quỷ Cẩu",
    36: "Quý Cô Thừa Kế", 37: "Ra Mắt Gia Tiên", 38: "Siêu Lừa Gặp Siêu Lầy", 39: "Siêu Trợ Lý",
    40: "Tấm Cám Chuyện Chưa Kể", 41: "Taxi Em Tên Gì", 42: "The Call", 43: "Thiên Mệnh Anh Hùng",
    44: "Tiểu Thư Và Ba Đầu Gấu", 45: "Trên Bàn Nhậu Dưới Bàn Mưu", 46: "Khác"
}

# ==== Load model và FAISS ====
def load_model_and_index():
    if not os.path.exists(INDEX_PATH) or not os.path.exists(LABEL_PATH):
        raise FileNotFoundError("❌ Không tìm thấy FAISS index hoặc labels.")

    model = call_model()
    index = faiss.read_index(INDEX_PATH)
    labels = np.load(LABEL_PATH)
    return model, index, labels

# ==== L2 normalize ====
def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)

# ==== Convert bất kỳ audio về WAV ====
def convert_to_wav(audio_path):
    y, sr = librosa.load(audio_path, sr=None)
    temp_wav = os.path.join(tempfile.gettempdir(), f"temp_{os.path.basename(audio_path)}.wav")
    sf.write(temp_wav, y, sr)
    return temp_wav

# ==== Tạo spectrogram ====
def generate_spectrogram(y, sr):
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    S_dB = librosa.power_to_db(S, ref=np.max)

    fig = plt.figure(figsize=(2.24, 2.24), dpi=100)
    librosa.display.specshow(S_dB, sr=sr, x_axis=None, y_axis=None)
    plt.axis('off')
    plt.tight_layout(pad=0)

    # Chuyển matplotlib figure thành ảnh numpy RGB
    canvas = FigureCanvas(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    buf.seek(0)
    image = Image.open(buf).convert("RGB")
    plt.close(fig)

    img_array = np.array(image.resize((224, 224)))
    return img_array

# ==== Cắt audio thành 10 đoạn 10s cách nhau 1s, từ giữa file ====
def split_audio_segments(wav_path, segment_duration=10.0, num_segments=10, hop_seconds=1.0):
    y, sr = librosa.load(wav_path, sr=22050)
    total_samples = len(y)
    segment_samples = int(segment_duration * sr)
    hop_samples = int(hop_seconds * sr)

    segments = []
    for i in range(num_segments):
        start = i * hop_samples
        end = start + segment_samples

        if start >= total_samples:
            break

        segment = y[start:end]
        if len(segment) < segment_samples:
            segment = np.pad(segment, (0, segment_samples - len(segment)), mode='constant')
        segments.append(segment)

    return segments, sr

# ==== Chuyển mỗi đoạn thành ảnh log-mel và batch CNN input ====
def segments_to_cnn_input(segments, sr):
    batch = []
    for y in segments:
        img = generate_spectrogram(y, sr)  # trả về ảnh RGB
        batch.append(img)
    x = np.array(batch)
    x = preprocess_input(x)
    return x

# ==== Dự đoán từ batch feature ====
def predict_from_feature_batch(features, index, index_labels, n_movies, similarity_threshold):
    features = l2_normalize(features.astype(np.float32))
    D, I = index.search(features, n_movies)  

    all_predictions = []
    priority_predictions = []  # chứa phim có dist == 0.99

    for distances, indices in zip(D, I):  
        for dist, idx in zip(distances, indices): 
            sim = 1 - dist / 2

            pred_data = index_labels[idx]
            if isinstance(pred_data, (np.ndarray, list)) and len(pred_data) > 1:
                pred_label = int(np.argmax(pred_data)) + 1
            else:
                pred_label = int(pred_data)

            film_name = CLASSES.get(pred_label, "Khác")

            # Nếu dist == 0.99 thì thêm vào danh sách ưu tiên
            if dist > 0.98:
                priority_predictions.append(film_name)

            # Các trường hợp còn lại xử lý như bình thường
            elif sim >= similarity_threshold:
                all_predictions.append(film_name)
            else:
                all_predictions.append(CLASSES.get(46, "Khác"))

    counts = Counter(all_predictions)

    # Lấy top-n_movies phim thường xuyên nhất (bỏ qua priority đã có)
    sorted_films = sorted(counts.items(), key=lambda item: (-item[1], all_predictions.index(item[0])))
    normal_results = [film for film, _ in sorted_films if film not in priority_predictions]

    # Kết quả cuối: Ưu tiên phim có dist = 0.99, sau đó đến phim thường
    result = priority_predictions + normal_results
    return result[:n_movies]

# ==== Hàm chính ====
def predict_film_from_audio(audio_path, similarity_threshold, n_movies):
    model, index, index_labels = load_model_and_index()
    try:
        start = time.time()
        wav_path = convert_to_wav(audio_path)
        segments, sr = split_audio_segments(wav_path)
        cnn_input = segments_to_cnn_input(segments, sr)
        features = model.predict(cnn_input, verbose=0)
        result = predict_from_feature_batch(features, index, index_labels, n_movies, similarity_threshold)
        print(f"Thời gian xử lý: {time.time() - start:.2f} giây")
        return result
    except Exception as e:
        return [f"❌ Lỗi xử lý âm thanh: {e}"]

# ==== Test ====
# if __name__ == "__main__":
#     test_audio = os.path.join(BASE_DIR, "img_test/0_scene_0880.mp3")
#     result = predict_film_from_audio(test_audio, 0.8, 1)
#     print("🎬 Dự đoán:", result)
