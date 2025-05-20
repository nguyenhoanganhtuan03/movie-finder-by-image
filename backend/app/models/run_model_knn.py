import os
import time
import numpy as np
import cv2
from collections import Counter

import onnxruntime as ort
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.preprocessing import image

# ==== Cấu hình ====
image_size = 128
base_dir = os.path.dirname(os.path.abspath(__file__))
knn_model_path = os.path.join(base_dir, "features_knn_more_data/resnet50/knn_model.onnx")

# ==== Load model ResNet50 để trích xuất đặc trưng ====
model = ResNet50(include_top=False, weights='imagenet', pooling='avg', input_shape=(image_size, image_size, 3))

# ==== Load mô hình KNN ONNX ====
ort_session = ort.InferenceSession(knn_model_path)

# ==== Danh sách phim ====
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
    41: "Tieu_Thu_Va_Ba_Dau_Gau", 42: "Tren_Ban_Nhau_Duoi_Ban_Muu"
}


# ==== Hàm trích xuất đặc trưng từ ảnh ====
def extract_features_from_image_array(img_array):
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    features = model.predict(img_array, verbose=0)
    return features


# ==== Hàm dự đoán bằng ONNX ====
def predict_knn_onnx(feature_vector):
    inputs = {ort_session.get_inputs()[0].name: feature_vector.astype(np.float32)}
    outputs = ort_session.run(None, inputs)

    if outputs[0].ndim == 2:
        return np.argmax(outputs[0][0]) + 1
    else:
        return outputs[0][0]


# ==== Hàm dự đoán từ ảnh ====
def predict_film_from_image(img_path):
    img = image.load_img(img_path, target_size=(image_size, image_size))
    img_array = image.img_to_array(img)
    feature_vector = extract_features_from_image_array(img_array)

    label_id = predict_knn_onnx(feature_vector)

    return classes.get(label_id, "Không xác định")


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
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        feature_vector = extract_features_from_image_array(frame)
        label_id = predict_knn_onnx(feature_vector)
        predictions.append(label_id)

    cap.release()

    if not predictions:
        return "❌ Không đọc được frame hợp lệ nào."

    # Chọn nhãn phổ biến nhất
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
if __name__ == "__main__":
    input_path = os.path.join(base_dir, "img_test/sieu_tro_ly (2).jpg")
    predicted_film = predict_film_auto(input_path)
    print(f"🎬 Dự đoán: {predicted_film}")
