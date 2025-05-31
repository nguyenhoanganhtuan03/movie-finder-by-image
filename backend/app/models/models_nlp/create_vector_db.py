import os
import json
import numpy as np
import faiss
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

# ========== Cấu hình ==========
VECTOR_PATH = "vector_db/vector_similarity.faiss"
METADATA_PATH = "vector_db/movie_metadata.json"
DB_NAME = "movie_database"
COLLECTION_NAME = "movies"
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ========== Chuẩn bị thư mục ==========
os.makedirs(os.path.dirname(VECTOR_PATH), exist_ok=True)

# ========== Kết nối MongoDB ==========
client = MongoClient("mongodb://localhost:27017/")
collection = client[DB_NAME][COLLECTION_NAME]

# ========== Load model ==========
model = SentenceTransformer(EMBEDDING_MODEL)
model.max_seq_length = 2048

# ========== Hàm xử lý ==========
def chunk_text(text, max_tokens=2048):
    sentences = text.split(". ")
    chunks, current = [], ""
    for sentence in sentences:
        if len(current + sentence) > max_tokens:
            chunks.append(current.strip())
            current = sentence + ". "
        else:
            current += sentence + ". "
    if current:
        chunks.append(current.strip())
    return chunks

def encode_long_text(text, model):
    chunks = chunk_text(text)
    embeddings = model.encode(chunks)
    return np.mean(embeddings, axis=0)

def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)

# ========== Chuẩn bị dữ liệu ==========

text_embeddings = []
metadata = []

for doc in collection.find():
    name = doc.get("name", "")
    duration = str(doc.get("duration", ""))
    director = doc.get("director", "")
    actors = ", ".join(doc.get("actor", []))
    genre = ", ".join(doc.get("genre", []))
    year = str(doc.get("year_of_release", ""))
    describe_text = doc.get("describe", "")

    # ⚠️ Sửa tên trường theo format query của mô hình
    attributes = {
        "diễn viên": actors,
        "thể loại": genre,
        "đạo diễn": director,
        "nội dung": describe_text,
        "năm phát hành": year
    }

    for attr_name, attr_value in attributes.items():
        if not attr_value.strip():
            continue  # bỏ qua nếu trống

        # Nhúng với context gồm tên phim + tên thuộc tính
        text_to_embed = f"Tên phim: {name}. {attr_name.capitalize()}: {attr_value}".lower()
        embedding = encode_long_text(text_to_embed, model)
        text_embeddings.append(embedding)

        metadata.append({
            "movie_name": name,
            "attribute": attr_name,
            "attribute_value": attr_value
        })

# ========== Tạo FAISS index ==========
embedding_matrix = l2_normalize(np.array(text_embeddings).astype("float32"))
dimension = embedding_matrix.shape[1]

index = faiss.IndexFlatL2(dimension)
index.add(embedding_matrix)

# ========== Lưu index và metadata ==========
faiss.write_index(index, VECTOR_PATH)
with open(METADATA_PATH, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print("✅ Đã lưu xong FAISS index và metadata với embedding từng thuộc tính.")
