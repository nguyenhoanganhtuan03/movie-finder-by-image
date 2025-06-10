import os
import time
import numpy as np
import faiss
import cv2
from collections import Counter, OrderedDict

from tensorflow.keras.applications import ResNet50, VGG16
# from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.applications.vgg16 import preprocess_input
from tensorflow.keras.preprocessing import image

# ==== Cấu hình ====
image_size = 224
base_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(base_dir, "faiss_224/vgg16/faiss_features.index")
label_path = os.path.join(base_dir, "faiss_224/vgg16/faiss_labels.npy")
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
    1: "21_Ngay_Yeu_Em",
    2: "4_Nam_2_Chang_1_Tinh_Yeu",
    3: "An_Tet_Ben_Con",
    4: "Bay_Ngot_Ngao",
    5: "Benh_Vien_Ma",
    6: "Bi_Mat_Lai_Bi_Mat",
    7: "Bi_Mat_Trong_Suong_Mu",
    8: "Bo_Tu_Oan_Gia",
    9: "Cho_Em_Den_Ngay_Mai",
    10: "Chu_Tich_Giao_Hang",
    11: "Chuyen_Tet",
    12: "Co_Ba_Sai_Gon",
    13: "Dao_Pho_Va_Piano",
    14: "Dat_Rung_Phuong_Nam",
    15: "Dia_Dao",
    16: "Dinh_Menh_Thien_Y",
    17: "Doi_Mat_Am_Duong",
    18: "Em_Chua_18",
    19: "Em_La_Cua_Em",
    20: "Gai_Gia_Lam_Chieu_3",
    21: "Gia_Ngheo_Gap_Phat",
    22: "Hem_Cut",
    23: "Hoan_Doi",
    24: "Ke_An_Danh",
    25: "Ke_An_Hon",
    26: "Lam_Giau_Voi_Ma",
    27: "Lat_Mat_1",
    28: "Lo_Mat",
    29: "Ma_Da",
    30: "Mat_Biec",
    31: "Nghe_Sieu_De",
    32: "Nhung_Nu_Hon_Ruc_Ro",
    33: "Ong_Ngoai_Tuoi_30",
    34: "Phap_Su_Tap_Su",
    35: "Quy_Cau",
    36: "Quy_Co_Thua_Ke",
    37: "Ra_Mat_Gia_Tien",
    38: "Sieu_Lua_Gap_Sieu_Lay",
    39: "Sieu_Tro_Ly",
    40: "Tam_Cam_Chuyen_Chua_Ke",
    41: "Taxi_Em_Ten_Gi",
    42: "The_Call",
    43: "Thien_Menh_Anh_Hung",
    44: "Tieu_Thu_Va_Ba_Dau_Gau",
    45: "Tren_Ban_Nhau_Duoi_Ban_Muu",
    46: "Khac"
}

# Chuẩn hóa L2 cho mỗi vector (độ dài = 1)
def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)  

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

    k = 5
    D, I = index.search(feature, k)

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

# Hàm xử lý video
def predict_film_from_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return ["❌ Không mở được video."]

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        return ["❌ Video không có frame nào."]

    frame_indices = [
        0,
        total_frames // 4,
        total_frames // 2,
        (3 * total_frames) // 4,
        total_frames - 1
    ]
    
    film_occurrences = []  # Lưu thứ tự xuất hiện
    film_counts = Counter()

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (image_size, image_size))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        x = np.expand_dims(frame, axis=0)
        x = preprocess_input(x)

        feature = model.predict(x, verbose=0)
        feature = l2_normalize(feature)
        feature = feature.astype(np.float32)

        k = 5
        D, I = index.search(feature, k)
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

    # Sắp xếp theo: số lần xuất hiện giảm dần, sau đó theo thứ tự xuất hiện đầu tiên
    unique_ordered_films = list(OrderedDict.fromkeys(film_occurrences))
    sorted_films = sorted(
        film_counts.items(),
        key=lambda item: (-item[1], unique_ordered_films.index(item[0]))
    )

    result = [film for film, _ in sorted_films[:4]]
    return result


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
# if __name__ == "__main__":
#     input_path = os.path.join(base_dir, "img_test/mada.mp4")
#     predicted_film = predict_film_auto(input_path)
#     print(f"🎬 Dự đoán: {predicted_film}")
