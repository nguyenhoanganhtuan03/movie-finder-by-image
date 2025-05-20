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
    1: "21_Ngay_Yeu_Em", 2: "An_Tet_Ben_Con", 3: "Bay_Ngot_Ngao", 4: "Benh_Vien_Ma",
    5: "Bi_Mat_Lai_Bi_Mat", 6: "Bi_Mat_Trong_Suong_Mu", 7: "Bo_Tu_Oan_Gia", 8: "Cho_Em_Den_Ngay_Mai",
    9: "Chu_Tich_Giao_Hang", 10: "Chuyen_Tet", 11: "Co_Ba_Sai_Gon", 12: "Dao_Pho_Va_Piano",
    13: "Dat_Phuong_Nam", 14: "Dia_Dao", 15: "Dinh_Menh_Thien_Y", 16: "Em_Chua_18",
    17: "Em_La_Cua_Em", 18: "Gai_Gia_Lam_Chieu_3", 19: "Gia_Ngheo_Gap_Phat", 20: "Hem_Cut",
    21: "Hoan_Doi", 22: "Ke_An_Danh", 23: "Ke_An_Hon", 24: "Lam_Giau_Voi_Ma",
    25: "Lat_Mat_1", 26: "Lo_Mat", 27: "Ma_Da", 28: "Mat_Biec",
    29: "Nhung_Nu_Hon_Ruc_Ro", 30: "Oan_Linh__Phan_1", 31: "Ong_Ngoai_Tuoi_30",
    32: "Phap_Su_Tap_Su", 33: "Quy_Co_Thua_Ke", 34: "Ra_Mat_Gia_Tien",
    35: "Sieu_Lua_Gap_Sieu_Lay", 36: "Sieu_Quay", 37: "Sieu_Tro_Ly",
    38: "Taxi_Em_Ten_Gi", 39: "The_Call", 40: "Thien_Menh_Anh_Hung",
    41: "Tieu_Thu_Va_Ba_Dau_Gau", 42: "Tren_Ban_Nhau_Duoi_Ban_Muu", 43: "Khac"
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

    frame_indices = [0, total_frames // 2, total_frames - 1]
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

        feature = model.predict(x, verbose=0).astype(np.float32)
        D, I = index.search(feature, 1)

        label_data = index_labels[I[0][0]]
        if isinstance(label_data, (np.ndarray, list)) and len(label_data) > 1:
            label_id = int(np.argmax(label_data)) + 1
        else:
            label_id = int(label_data)

        predictions.append(label_id)

    cap.release()

    if not predictions:
        return "❌ Không đọc được frame hợp lệ nào."

    # Lấy nhãn có nhiều vote nhất
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
input_path = os.path.join(base_dir, "img_test/taxi_em_ten_gi.jpg")
predicted_film = predict_film_auto(input_path)
print(f"🎬 Dự đoán: {predicted_film}")
