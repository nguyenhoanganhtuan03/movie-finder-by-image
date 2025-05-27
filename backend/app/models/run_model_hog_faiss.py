import os
import time
import numpy as np
import cv2
import traceback
from collections import Counter

from tensorflow.keras.preprocessing import image
from skimage.feature import hog
from skimage import color
import faiss

# ==== Cấu hình ====
image_size = 128
similarity_threshold = 0.8
base_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(base_dir, "features_faiss_more_data/hog/faiss_features.index")
label_path = os.path.join(base_dir, "features_faiss_more_data/hog/faiss_labels.npy")

# ==== Load FAISS index, labels, và KMeans ONNX model ====
if not os.path.exists(index_path):
    print(f"❌ Không tìm thấy FAISS index tại: {index_path}")
    exit()
if not os.path.exists(label_path):
    print(f"❌ Không tìm thấy nhãn tại: {label_path}")
    exit()

try:
    # Load FAISS index
    index = faiss.read_index(index_path)

    # Load labels
    index_labels = np.load(label_path)

    print(f"✅ FAISS index đã được tải thành công!")
    print(f"   - Số lượng vectors: {index.ntotal}")
    print(f"   - Kích thước vector: {index.d}")

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
    26: "Làm Giàu Với Ma", 27: "Lật Mặt 1", 28: "Linh Miêu Quỷ Nhập Tràng", 29: "Lộ Mặt", 30: "Ma Da",
    31: "Mắt Biếc", 32: "Nghề Siêu Dễ", 33: "Những Nụ Hôn Rực Rỡ", 34: "Ông Ngoại Tuổi 30", 35: "Pháp Sư Tập Sự",
    36: "Quý Cô Thừa Kế", 37: "Ra Mắt Gia Tiên", 38: "Siêu Lừa Gặp Siêu Lầy", 39: "Siêu Trợ Lý", 40: "Tấm Cám Chuyện Chưa Kể",
    41: "Taxi Em Tên Gì", 42: "The Call", 43: "Thiên Mệnh Anh Hùng", 44: "Tiểu Thư Và Ba Đầu Gấu", 45: "Trên Bàn Nhậu Dưới Bàn Mưu",
    46: "Khác"
}

# Trích đặc trưng với HOG
def extract_hog_features(gray, img_path=None):
    """Trích xuất vector HOG từ ảnh xám"""
    try:
        hog_vector = hog(gray,
                         orientations=8,
                         pixels_per_cell=(16, 16),
                         cells_per_block=(2, 2),
                         block_norm='L2-Hys',
                         feature_vector=True)

        if hog_vector is None or len(hog_vector) == 0:
            return None

        return hog_vector.astype(np.float32)

    except Exception as e:
        if img_path:
            print(f"Lỗi trích xuất HOG từ {img_path}: {e}")
        else:
            print(f"Lỗi trích xuất HOG: {e}")
        return None

# ==== Hàm dự đoán từ ảnh ====
def predict_film_from_image(img_path):
    img = image.load_img(img_path, target_size=(image_size, image_size))
    img_array = image.img_to_array(img)
    gray = color.rgb2gray(img_array)
    feature = extract_hog_features(gray, img_path)
    
    if feature is None:
        return "❌ Không trích xuất được đặc trưng từ ảnh."

    feature = feature / (np.linalg.norm(feature) + 1e-10)
    feature = feature.reshape(1, -1).astype(np.float32)

    D, I = index.search(feature, 1)

    euclidean_dist_squared = D[0][0]
    similarity_score = 1 - euclidean_dist_squared / 2

    if similarity_score < similarity_threshold:
        pred_label = 46
    else:
        pred_label_data = index_labels[I[0][0]]
        pred_label = int(np.argmax(pred_label_data)) + 1 if isinstance(pred_label_data, (np.ndarray, list)) and len(pred_label_data) > 1 else int(pred_label_data) + 1

    return classes.get(pred_label, "Không xác định")


# ==== Hàm dự đoán từ video ====
def predict_film_from_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return "❌ Không mở được video."

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        return "❌ Video không có frame nào."

    frame_indices = [0, total_frames // 2, total_frames - 1]
    predictions = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue

        resized = cv2.resize(frame, (image_size, image_size))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        gray = gray / 255.0  # Normalize to [0, 1] for consistency with skimage

        feature = extract_hog_features(gray)

        if feature is None:
            continue

        feature = feature / (np.linalg.norm(feature) + 1e-10)
        feature = feature.reshape(1, -1).astype(np.float32)

        D, I = index.search(feature, 1)

        euclidean_dist_squared = D[0][0]
        similarity_score = 1 - euclidean_dist_squared / 2

        if similarity_score < similarity_threshold:
            pred_label = 46
        else:
            pred_label_data = index_labels[I[0][0]]
            pred_label = int(np.argmax(pred_label_data)) + 1 if isinstance(pred_label_data, (np.ndarray, list)) and len(pred_label_data) > 1 else int(pred_label_data) + 1
        predictions.append(pred_label)

    cap.release()

    if not predictions:
        return "❌ Không đọc được frame hợp lệ nào."

    most_common_id = Counter(predictions).most_common(1)[0][0]
    return classes.get(most_common_id, "Không xác định")

# ==== Hàm tự động xử lý ảnh hoặc video ====
def predict_film_auto(input_path):
    try:
        start_time = time.time()
        ext = os.path.splitext(input_path)[-1].lower()

        if ext in ['.jpg', '.jpeg', '.png']:
            film_name = predict_film_from_image(input_path)
        elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
            film_name = predict_film_from_video(input_path)
        else:
            return "❌ Định dạng không hỗ trợ."

        end_time = time.time()
        print(f"⏱️ Thời gian xử lý: {end_time - start_time:.4f} giây")
        return film_name

    except Exception as e:
        return f"❌ Lỗi khi xử lý: {e}"

# ==== Test thử ====
# if __name__ == "__main__":
#     input_path = os.path.join(base_dir, "img_test/chu_tich_giao_hang.mp4")
#     predicted_film = predict_film_auto(input_path)
#     print(f"🎬 Dự đoán: {predicted_film}")
