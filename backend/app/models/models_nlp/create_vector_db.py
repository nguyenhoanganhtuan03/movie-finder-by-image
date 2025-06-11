import os
import csv
import numpy as np
import faiss
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

# ========== CẤU HÌNH ==========
VECTOR_DIR = "vector_db"
INDEX_PATH = os.path.join(VECTOR_DIR, "index_movie.faiss")
LABELS_MAPPING_PATH = os.path.join(VECTOR_DIR, "labels_mapping.csv")
LABELS_ARRAY_PATH = os.path.join(VECTOR_DIR, "labels_array.npy")
METADATA_PATH = os.path.join(VECTOR_DIR, "metadata.csv")
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
DB_NAME = "movie_database"
COLLECTION_NAME = "movies"

# ========== CHUẨN BỊ ==========
os.makedirs(VECTOR_DIR, exist_ok=True)
client = MongoClient("mongodb://localhost:27017/")
collection = client[DB_NAME][COLLECTION_NAME]
model = SentenceTransformer(EMBEDDING_MODEL)
model.max_seq_length = 2048

# ========== HÀM TIỆN ÍCH ==========
def embed_text(text):
    text = text.strip().lower()
    return model.encode(text, convert_to_numpy=True)

def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)

def save_labels_mapping(path, labels_list):
    with open(path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["index", "name"])
        for idx, name in enumerate(labels_list):
            writer.writerow([idx, name])

def save_metadata_csv(path, metadata_list):
    with open(path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "index", "name", "genres", "duration", "director",
            "actors", "year", "description"
        ])
        for idx, item in enumerate(metadata_list):
            writer.writerow([
                idx,
                item.get("name", ""),
                item.get("genres", ""),
                item.get("duration", ""),
                item.get("director", ""),
                item.get("actors", ""),
                item.get("year", ""),
                item.get("description", ""),
            ])

# ========== XỬ LÝ DỮ LIỆU ==========
vectors = []
labels = []
metadata_list = []

for doc in collection.find():
    try:
        name = doc.get("name", "").strip()
        if not name:
            continue

        genres = ', '.join(doc.get("genre", [])).strip()
        duration = str(doc.get("duration", "")).strip()
        director = doc.get("director", "").strip()
        actors = ', '.join(doc.get("actor", [])).strip()
        year = str(doc.get("year_of_release", "")).strip()
        description = doc.get("describe", "").strip()

        # Embed từng thuộc tính nếu tồn tại
        if genres:
            for genre in genres.split(','):
                genre = genre.strip()
                if genre:
                    vectors.append(embed_text(genre))
                    labels.append(name)

        if duration:
            vectors.append(embed_text(duration))
            labels.append(name)

        if director:
            vectors.append(embed_text(director))
            labels.append(name)

        if actors:
            for actor in actors.split(','):
                actor = actor.strip()
                if actor:
                    vectors.append(embed_text(actor))
                    labels.append(name)

        if year:
            vectors.append(embed_text(year))
            labels.append(name)

        if description:
            vectors.append(embed_text(description))
            labels.append(name)

        # Lưu metadata
        metadata_list.append({
            "name": name,
            "genres": genres,
            "duration": duration,
            "director": director,
            "actors": actors,
            "year": year,
            "description": description,
        })

    except Exception as e:
        print(f"Lỗi khi xử lý phim '{doc.get('name', 'Unknown')}': {e}")

# ========== CHUẨN HÓA VECTOR & LƯU FAISS ==========
embedding_matrix = np.array(vectors).astype("float32")
embedding_matrix = l2_normalize(embedding_matrix)

index = faiss.IndexFlatL2(embedding_matrix.shape[1])
index.add(embedding_matrix)
faiss.write_index(index, INDEX_PATH)

# ========== LƯU FILE ==========
save_labels_mapping(LABELS_MAPPING_PATH, labels)
np.save(LABELS_ARRAY_PATH, np.array(labels))
save_metadata_csv(METADATA_PATH, metadata_list)

# ========== THỐNG KÊ ==========
print(f"Số lượng vector đã lưu: {len(labels)}")
print(f"Số lượng phim duy nhất: {len(metadata_list)}")
print("✅ Đã lưu FAISS index, labels mapping, labels array và metadata.")
