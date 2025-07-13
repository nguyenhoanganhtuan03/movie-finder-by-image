import os
import time
import numpy as np
import cv2
from collections import Counter, OrderedDict

from skimage.feature import hog
from skimage import color
import faiss

# ==== Cấu hình ====
image_size = 224
similarity_threshold = 0.8
base_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(base_dir, "faiss_224/hog/faiss_features.index")
label_path = os.path.join(base_dir, "faiss_224/hog/faiss_labels.npy")

# ==== Load FAISS index, labels ====
if not os.path.exists(index_path):
    print(f"❌ Không tìm thấy FAISS index tại: {index_path}")
    exit()
if not os.path.exists(label_path):
    print(f"❌ Không tìm thấy nhãn tại: {label_path}")
    exit()

try:
    index = faiss.read_index(index_path)
    index_labels = np.load(label_path)
except Exception as e:
    print(f"❌ Lỗi khi tải models: {e}")
    exit()

# ==== Danh sách phim ====
classes = {
    1: "21 Ngày Yêu Em", 2: "4 Năm 2 Chàng 1 Tình Yêu", 3: "Ăn Tết Bên Cồn", 4: "Bẫy Ngọt Ngào", 5: "Bệnh Viện Ma",
    6: "Bí Mật Lại Bị Mất", 7: "Bí Mật Trong Sương Mù", 8: "Bộ Tứ Oan Gia", 9: "Chờ Em Đến Ngày Mai", 10: "Chủ Tịch Giao Hàng",
    11: "Chuyện Tết", 12: "Cô Ba Sài Gòn", 13: "Đào, Phở Và Piano", 14: "Đất Rừng Phương Nam", 15: "Địa Đạo",
    16: "Định Mệnh Thiên Ý", 17: "Đôi Mắt Âm Dương", 18: "Em Chưa 18", 19: "Em Là Của Em", 20: "Gái Già Lắm Chiêu 3",
    21: "Giả Nghèo Gặp Phật", 22: "Hẻm Cụt", 23: "Hoán Đổi", 24: "Kẻ Ẩn Danh", 25: "Kẻ Ăn Hồn",
    26: "Làm Giàu Với Ma", 27: "Lật Mặt 1", 28: "Lộ Mặt", 29: "Ma Da", 30: "Mắt Biếc", 31: "Nghề Siêu Dễ", 32: "Những Nụ Hôn Rực Rỡ",
    33: "Ông Ngoại Tuổi 30", 34: "Pháp Sư Tập Sự", 35: "Quỷ Cẩu", 36: "Quý Cô Thừa Kế", 37: "Ra Mắt Gia Tiên",
    38: "Siêu Lừa Gặp Siêu Lầy", 39: "Siêu Trợ Lý", 40: "Tấm Cám Chuyện Chưa Kể",
    41: "Taxi Em Tên Gì", 42: "The Call", 43: "Thiên Mệnh Anh Hùng", 44: "Tiểu Thư Và Ba Đầu Gấu", 45: "Trên Bàn Nhậu Dưới Bàn Mưu",
    46: "Khác"
}

# Chuẩn hóa L2 cho mỗi vector (độ dài = 1)
def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)  # epsilon tránh chia cho 0

# ==== Hàm trích xuất đặc trưng HOG ====
def extract_hog_features(img_path):
    """Trích xuất vector HOG trực tiếp từ ảnh"""
    try:
        img = cv2.imread(img_path)
        if img is None:
            return None

        img = cv2.resize(img, (image_size, image_size))
        gray = color.rgb2gray(img)

        # Trích xuất đặc trưng HOG (vector 1 chiều)
        hog_vector = hog(gray,
                        orientations=9,                
                        pixels_per_cell=(24, 24),       
                        cells_per_block=(3, 3),
                        block_norm='L2-Hys',
                        feature_vector=True)

        if hog_vector is None or len(hog_vector) == 0:
            return None

        return hog_vector.astype(np.float32)

    except Exception as e:
        print(f"Lỗi trích xuất HOG từ {img_path}: {e}")
        return None

# ==== Hàm dự đoán từ ảnh ====
def predict_film_from_image(img_path, similarity_threshold, n_movies):
    img = cv2.imread(img_path)
    if img is None:
        return ["❌ Không đọc được ảnh."]

    feature = extract_hog_features(img_path)
    if feature is None:
        return ["❌ Không trích xuất được đặc trưng."]

    # Chuẩn hóa L2
    feature = feature / (np.linalg.norm(feature) + 1e-10)
    feature = feature.reshape(1, -1).astype(np.float32)
    D, I = index.search(feature, n_movies)
    similarity_scores = 1 - D[0] / 2

    result_labels = []
    seen_labels = set()

    for idx, sim in zip(I[0], similarity_scores):
        if sim < similarity_threshold:
            pred_label = 46
        else:
            pred_label_data = index_labels[idx]
            if isinstance(pred_label_data, (np.ndarray, list)) and len(pred_label_data) > 1:
                pred_label = int(np.argmax(pred_label_data)) + 1
            else:
                pred_label = int(pred_label_data)

        film_name = classes.get(pred_label, "Không xác định")
        if film_name not in seen_labels:
            result_labels.append(film_name)
            seen_labels.add(film_name)

    return result_labels

# ==== Hàm dự đoán từ video ====
def predict_film_from_video(video_path, similarity_threshold, n_movies):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return ["❌ Không mở được video."]

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        return ["❌ Video không có frame."]

    frame_indices = [0, total_frames // 4, total_frames // 2, (3 * total_frames) // 4, total_frames - 1]
    film_occurrences = []
    film_counts = Counter()

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue

        feature = extract_hog_features(video_path)
        if feature is None:
            continue

        feature = feature.reshape(1, -1)
        D, I = index.search(feature, n_movies)
        similarity_scores = 1 - D[0] / 2

        seen_in_frame = set()
        for idx_db, sim in zip(I[0], similarity_scores):
            if sim < similarity_threshold:
                pred_label = 46
            else:
                pred_label_data = index_labels[idx_db]
                if isinstance(pred_label_data, (np.ndarray, list)) and len(pred_label_data) > 1:
                    pred_label = int(np.argmax(pred_label_data)) + 1
                else:
                    pred_label = int(pred_label_data)

            film_name = classes.get(pred_label, "Không xác định")
            if film_name not in seen_in_frame:
                seen_in_frame.add(film_name)
                film_counts[film_name] += 1
                film_occurrences.append(film_name)

    cap.release()

    if not film_counts:
        return ["❌ Không đọc được frame hợp lệ nào."]

    unique_ordered_films = list(OrderedDict.fromkeys(film_occurrences))
    sorted_films = sorted(
        film_counts.items(),
        key=lambda item: (-item[1], unique_ordered_films.index(item[0]))
    )
    return [film for film, _ in sorted_films[:n_movies]]

# ==== Hàm tự nhận dạng ảnh hoặc video ====
def predict_film_auto(input_path, similarity_threshold, n_movies):
    try:
        start_time = time.time()
        ext = os.path.splitext(input_path)[-1].lower()

        if ext in ['.jpg', '.jpeg', '.png']:
            result = predict_film_from_image(input_path, similarity_threshold, n_movies)
        elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
            result = predict_film_from_video(input_path, similarity_threshold, n_movies)
        else:
            return ["❌ Định dạng không hỗ trợ."]

        end_time = time.time()
        print("=====Đặc trưng HOG=====")
        print(f"⏱ Thời gian xử lý: {end_time - start_time:.4f} giây")
        return result

    except Exception as e:
        return [f"❌ Lỗi khi xử lý: {e}"]

if __name__ == "__main__":
    test_path = os.path.join(base_dir, "img_test/lgvm.png")
    result = predict_film_auto(test_path, similarity_threshold=0.8, n_movies=5)
    print("🎬 Dự đoán:", result)
