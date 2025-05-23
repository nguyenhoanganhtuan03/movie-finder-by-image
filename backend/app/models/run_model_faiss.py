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
# Thêm Linh Miêu Quỷ Nhập Tràng, Đôi Mắt Âm Dương, Nghề Siêu Dễ, Tấm Cám Chuyện Chưa Kể
# Chạy lại Dataset
classes = {
    1: "21 Ngày yêu em", 2: "Ăn tết bên cồn", 3: "Bẫy ngọt ngào", 4: "Bệnh viện ma",
    5: "Bí mật lại bị mất", 6: "Bí mật trong sương mù", 7: "Bộ tứ oan gia", 8: "Chờ em đến ngày mai",
    9: "Chủ tịch giao hàng", 10: "Chuyện tết", 11: "Cô ba sài gòn", 12: "Đào, phở và piano",
    13: "Đất rừng phương nam", 14: "Địa đạo", 15: "Định mệnh thiên y", 16: "Em chưa 18",
    17: "Em là của em", 18: "Gái già lắm chiêu", 19: "Giả nghèo gặp phật", 20: "Hẻm cụt",
    21: "Hoán đổi", 22: "Kẻ ẩn danh", 23: "Kẻ ăn hồn", 24: "Làm giàu với ma",
    25: "Lật mặt 1", 26: "Lộ mặt", 27: "Ma da", 28: "Mắt biếc",
    29: "Những nụ hôn rực rỡ", 30: "Oán linh", 31: "Ông ngoại tuổi 30", 32: "Pháp sư tập sự",
    33: "Quý cô thừa kế", 34: "Ra mắt gia tiên", 35: "Siêu lừa gặp siêu lầy", 36: "4 năm 2 chàng 1 tình yêu",
    37: "Siêu trợ lý", 38: "Taxi em tên gì", 39: "The Call", 40: "Thiên mệnh anh hùng",
    41: "Tiểu thư và ba đầu gấu", 42: "Trên bàn nhậu dưới bàn mưu", 43: "Khác"
}

# Chuẩn hóa L2 cho mỗi vector (độ dài = 1)
def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)  # thêm epsilon để tránh chia cho 0

# ==== Hàm dự đoán ====
# Hàm xử lý ảnh
def predict_film_from_image(img_path):
    img = image.load_img(img_path, target_size=(image_size, image_size))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    feature = model.predict(x, verbose=0)
    feature = l2_normalize(feature)
    feature = feature.astype(np.float32)
    D, I = index.search(feature, 1)

    euclidean_dist_squared = D[0][0]
    similarity_score = 1 - euclidean_dist_squared / 2  # Chuyển đổi khoảng cách thành cosine similarity

    # Nếu similarity dưới ngưỡng, gán nhãn "Khác" (43)
    if similarity_score < similarity_threshold:
        pred_label = 43  # Nhãn "Khác"
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

        # Nếu similarity dưới ngưỡng, gán nhãn "Khác" (43)
        if similarity_score < similarity_threshold:
            pred_label = 43
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
        print(f"⏱️ Thời gian xử lý: {end_time - start_time:.4f} giây")
        return film_name

    except Exception as e:
        return f"❌ Lỗi khi xử lý: {e}"

# ==== Test ====
# input_path = os.path.join(base_dir, "img_test/4_2_1.jpg")
# predicted_film = predict_film_auto(input_path)
# print(f"🎬 Dự đoán: {predicted_film}")
