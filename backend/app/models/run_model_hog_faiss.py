import os
import time
import numpy as np
import cv2
from collections import Counter

from skimage.feature import hog
from skimage import color
import faiss

# ==== Cấu hình ====
image_size = 224
similarity_threshold = 0.8
base_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(base_dir, "faiss_224/hog/faiss_features.index")
label_path = os.path.join(base_dir, "faiss_224/hog/faiss_labels.npy")

# ==== Load FAISS index, labels, và KMeans ONNX model ====
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

# Trích đặc trưng với HOG
def extract_hog_features(gray, img_path=None):
    """Trích xuất vector HOG từ ảnh xám"""
    try:
        hog_vector = hog(            
            gray,
            orientations=9,                
            pixels_per_cell=(24, 24),       
            cells_per_block=(3, 3),
            block_norm='L2-Hys',
            feature_vector=True
        )

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
    img = cv2.imread(img_path)
    img = cv2.resize(img, (image_size, image_size))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
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
        print("=====Đặc trưng HOG=====")
        print(f"⏱️ Thời gian xử lý: {end_time - start_time:.4f} giây")
        return film_name

    except Exception as e:
        return f"❌ Lỗi khi xử lý: {e}"

# ==== Test thử ====
# if __name__ == "__main__":
#     input_path = os.path.join(base_dir, "img_test/lgvm.png")
#     predicted_film = predict_film_auto(input_path)
#     print(f"🎬 Dự đoán: {predicted_film}")
    
