import os
import time
import numpy as np
import faiss
import cv2
from collections import Counter

from tensorflow.keras.applications import ResNet50, VGG16
# from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.applications.vgg16 import preprocess_input
from tensorflow.keras.preprocessing import image

# ==== Cấu hình ====
image_size = 128
base_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(base_dir, "features_faiss_more_data/vgg16/faiss_features.index")
label_path = os.path.join(base_dir, "features_faiss_more_data/vgg16/faiss_labels.npy")
similarity_threshold = 0.8

# ==== Load model ResNet50 ====
# model = ResNet50(include_top=False, weights='imagenet', pooling='avg', input_shape=(image_size, image_size, 3))
model = VGG16(include_top=False, weights='imagenet', pooling='avg', input_shape=(image_size, image_size, 3))

# ==== Load FAISS index và labels ====
if not os.path.exists(index_path) or not os.path.exists(label_path):
    print("❌ Không tìm thấy FAISS index hoặc labels.")
    exit()

index = faiss.read_index(index_path)
index_labels = np.load(label_path)

# ==== Danh sách phim (mapping) ====
classes = {
    1: "21 Ngày Yêu Em", 2: "4 Năm 2 Chàng 1 Tình Yêu", 3: "Ăn Tết Bên Cồn", 4: "Bẫy Ngọt Ngào", 5: "Bệnh Viện Ma",
    6: "Bí Mật Lại Bị Mất", 7: "Bí Mật Trong Sương Mù", 8: "Bộ Tứ Oan Gia", 9: "Chờ Em Đến Ngày Mai", 10: "Chủ Tịch Giao Hàng",
    11: "Chuyện Tết", 12: "Cô Ba Sài Gòn", 13: "Đào, Phở Và Piano", 14: "Đất Rừng Phương Nam", 15: "Địa Đạo",
    16: "Định Mệnh Thiên Ý", 17: "Đôi Mắt Âm Dương", 18: "Em Chưa 18", 19: "Em Là Của Em", 20: "Gái Già Lắm Chiêu 3",
    21: "Giả Nghèo Gặp Phật", 22: "Hẻm Cụt", 23: "Hoán Đổi", 24: "Kẻ Ẩn Danh", 25: "Kẻ Ăn Hồn",
    26: "Làm Giàu Với Ma", 27: "Lật Mặt 1", 28: "Linh Miêu: Quỷ Nhập Tràng", 29: "Lộ Mặt", 30: "Ma Da",
    31: "Mắt Biếc", 32: "Nghề Siêu Dễ", 33: "Những Nụ Hôn Rực Rỡ", 34: "Ông Ngoại Tuổi 30", 35: "Pháp Sư Tập Sự",
    36: "Quý Cô Thừa Kế", 37: "Ra Mắt Gia Tiên", 38: "Siêu Lừa Gặp Siêu Lầy", 39: "Siêu Trợ Lý", 40: "Tấm Cám: Chuyện Chưa Kể",
    41: "Taxi Em Tên Gì", 42: "The Call", 43: "Thiên Mệnh Anh Hùng", 44: "Tiểu Thư Và Ba Đầu Gấu", 45: "Trên Bàn Nhậu Dưới Bàn Mưu",
    46: "Khác"
}

# Chuẩn hóa L2 cho mỗi vector (độ dài = 1)
def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)  # thêm epsilon để tránh chia cho 0

# ==== Hàm dự đoán ====
# Hàm xử lý ảnh
def predict_film_from_image(img_path):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (image_size, image_size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    feature = model.predict(x, verbose=0)
    feature = l2_normalize(feature)
    feature = feature.astype(np.float32)
    D, I = index.search(feature, 1)

    euclidean_dist_squared = D[0][0]
    similarity_score = 1 - euclidean_dist_squared / 2  # Chuyển đổi khoảng cách thành cosine similarity

    # Nếu similarity dưới ngưỡng, gán nhãn "Khác"
    if similarity_score < similarity_threshold:
        pred_label = 46  # Nhãn "Khác"
    else:
        # Lấy nhãn dự đoán từ FAISS
        pred_label_data = index_labels[I[0][0]]
        if isinstance(pred_label_data, (np.ndarray, list)) and len(pred_label_data) > 1:
            pred_label = int(np.argmax(pred_label_data)) + 1
        else:
            pred_label = int(pred_label_data)

    film_name = classes.get(pred_label, "Không xác định")
    return film_name

# Hàm xử lý video
def predict_film_from_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return "❌ Không mở được video."

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        return "❌ Video không có frame nào."

    # 5 frame
    frame_indices = [
        0,
        total_frames // 4,
        total_frames // 2,
        (3 * total_frames) // 4,
        total_frames - 1
    ]
    predictions = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue  # Bỏ qua nếu không đọc được frame

        frame = cv2.resize(frame, (image_size, image_size))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        x = np.expand_dims(frame, axis=0)
        x = preprocess_input(x)

        feature = model.predict(x, verbose=0)
        feature = l2_normalize(feature)
        feature = feature.astype(np.float32)
        D, I = index.search(feature, 1)

        euclidean_dist_squared = D[0][0]
        similarity_score = 1 - euclidean_dist_squared / 2  # Chuyển đổi khoảng cách thành cosine similarity

        # Nếu similarity dưới ngưỡng, gán nhãn "Khác"
        if similarity_score < similarity_threshold:
            pred_label = 46
        else:
            # Lấy nhãn dự đoán từ FAISS
            pred_label_data = index_labels[I[0][0]]
            if isinstance(pred_label_data, (np.ndarray, list)) and len(pred_label_data) > 1:
                pred_label = int(np.argmax(pred_label_data)) + 1
            else:
                pred_label = int(pred_label_data)

        predictions.append(pred_label)

    cap.release()

    if not predictions:
        return "❌ Không đọc được frame hợp lệ nào."

    most_common_id = Counter(predictions).most_common(1)[0][0]
    film_name = classes.get(most_common_id, "Không xác định")
    return film_name


# Hàm tự động nhận biết loại file và xử lý
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
        print("=====Đặc trưng CNN=====")
        print(f"⏱️ Thời gian xử lý: {end_time - start_time:.4f} giây")
        return film_name

    except Exception as e:
        return f"❌ Lỗi khi xử lý: {e}"

# ==== Test ====
if __name__ == "__main__":
    input_path = os.path.join(base_dir, "img_test/elce.jpg")
    predicted_film = predict_film_auto(input_path)
    print(f"🎬 Dự đoán: {predicted_film}")
