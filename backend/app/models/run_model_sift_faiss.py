import os
import time
import numpy as np
import cv2
from collections import Counter

import onnxruntime as ort
from sklearn.preprocessing import normalize
import faiss

# ==== Cấu hình ====
image_size = 128
n_clusters = 128
similarity_threshold = 0.8
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "features_faiss_more_data/sift/kmeans_model.onnx")
index_path = os.path.join(base_dir, "features_faiss_more_data/sift/faiss_features.index")
label_path = os.path.join(base_dir, "features_faiss_more_data/sift/faiss_labels.npy")

# ==== Load FAISS index, labels, và KMeans ONNX model ====
if not os.path.exists(index_path):
    print(f"❌ Không tìm thấy FAISS index tại: {index_path}")
    exit()
if not os.path.exists(label_path):
    print(f"❌ Không tìm thấy nhãn tại: {label_path}")
    exit()
if not os.path.exists(model_path):
    print(f"❌ Không tìm thấy KMeans ONNX model tại: {model_path}")
    exit()

try:
    # Load FAISS index
    index = faiss.read_index(index_path)

    # Load labels
    index_labels = np.load(label_path)

    # Load KMeans ONNX model
    kmeans_session = ort.InferenceSession(model_path)

    print(f"✅ FAISS index đã được tải thành công!")
    print(f"   - Số lượng vectors: {index.ntotal}")
    print(f"   - Kích thước vector: {index.d}")
    print(f"✅ KMeans ONNX model đã được tải thành công!")

except Exception as e:
    print(f"❌ Lỗi khi tải models: {e}")
    exit()

# ==== Khởi tạo SIFT detector ====
sift = cv2.SIFT_create()

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

# Hàm trích xuất đặc trưng SIFT BOW cho một ảnh
def extract_sift_bow_features(gray, sift_detector, kmeans_session, n_clusters):
    """Trích xuất đặc trưng SIFT BOW từ ảnh grayscale"""
    try:
        keypoints, descriptors = sift_detector.detectAndCompute(gray, None)

        if descriptors is None or len(descriptors) == 0:
            return np.zeros(n_clusters, dtype=np.float32)

        # Dự đoán cluster bằng KMeans ONNX
        input_name = kmeans_session.get_inputs()[0].name
        clusters = kmeans_session.run(None, {input_name: descriptors.astype(np.float32)})[0]

        # clusters là mảng nhãn cluster mỗi descriptor
        hist = np.zeros(n_clusters)
        for c in clusters:
            hist[int(c)] += 1

        # Chuẩn hóa L2
        hist = normalize(hist.reshape(1, -1), norm='l2')[0]
        return hist.astype(np.float32)

    except Exception as e:
        print(f"Lỗi trích xuất đặc trưng: {e}")
        return None

# ==== Hàm dự đoán từ ảnh ====
def predict_film_from_image(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return "❌ Không đọc được ảnh."

    img = cv2.resize(img, (image_size, image_size))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    feature = extract_sift_bow_features(gray, sift, kmeans_session, n_clusters)
    if feature is None:
        return "❌ Không trích xuất được đặc trưng."

    feature = feature / (np.linalg.norm(feature) + 1e-10)
    feature = feature.reshape(1, -1).astype(np.float32)

    D, I = index.search(feature, 1)
    euclidean_dist_squared = D[0][0]
    similarity_score = 1 - euclidean_dist_squared / 2

    if similarity_score < similarity_threshold:
        pred_label = 46  # "Khác"
    else:
        pred_label_data = index_labels[I[0][0]]
        if isinstance(pred_label_data, (np.ndarray, list)) and len(pred_label_data) > 1:
            pred_label = int(np.argmax(pred_label_data)) + 1
        else:
            pred_label = int(pred_label_data) + 1

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

        frame = cv2.resize(frame, (image_size, image_size))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        feature = extract_sift_bow_features(gray, sift, kmeans_session, n_clusters)
        if feature is None:
            continue

        feature = feature / (np.linalg.norm(feature) + 1e-10)
        feature = feature.reshape(1, -1).astype(np.float32)

        D, I = index.search(feature, 1)
        euclidean_dist_squared = D[0][0]
        similarity_score = 1 - euclidean_dist_squared / 2

        if similarity_score < similarity_threshold:
            pred_label = 46  # "Khác"
        else:
            pred_label_data = index_labels[I[0][0]]
            if isinstance(pred_label_data, (np.ndarray, list)) and len(pred_label_data) > 1:
                pred_label = int(np.argmax(pred_label_data)) + 1
            else:
                pred_label = int(pred_label_data) + 1

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
        print("=====Đặc trưng SIFT + KMeans=====")
        print(f"⏱️ Thời gian xử lý: {end_time - start_time:.4f} giây")
        return film_name

    except Exception as e:
        return f"❌ Lỗi khi xử lý: {e}"


# ==== Test thử ====
# if __name__ == "__main__":
#     input_path = os.path.join(base_dir, "img_test/chu_tich_giao_hang.mp4")
#     predicted_film = predict_film_auto(input_path)
#     print(f"🎬 Dự đoán: {predicted_film}")
    
