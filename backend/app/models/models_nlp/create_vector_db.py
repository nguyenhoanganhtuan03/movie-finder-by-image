import os
import csv
import numpy as np
import faiss
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from pyvi.ViTokenizer import tokenize

# ========== CẤU HÌNH ==========
VECTOR_DIR = "vector_db"
INDEX_PATH = os.path.join(VECTOR_DIR, "index_movie.faiss")
PROMPT_MAPPING_PATH = os.path.join(VECTOR_DIR, "prompt_mapping.csv")
METADATA_PATH = os.path.join(VECTOR_DIR, "metadata.csv")
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
# EMBEDDING_MODEL = "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
DB_NAME = "movie_database"
COLLECTION_NAME = "movies"

# ========== CHUẨN BỊ ==========
os.makedirs(VECTOR_DIR, exist_ok=True)
client = MongoClient("mongodb://localhost:27017/")
collection = client[DB_NAME][COLLECTION_NAME]
model = SentenceTransformer(EMBEDDING_MODEL)
model.max_seq_length = 2048

# ========== HÀM TIỆN ÍCH ==========
# def embed_text(text):
#     text = text.strip().lower()
#     sentences = [tokenize(text)]
#     return model.encode(sentences, convert_to_numpy=True)[0]

def embed_text(text):
    text = text.strip().lower()
    return model.encode(text, convert_to_numpy=True)

def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)

def truncate_prompt(prompt, max_chars=6000):
    return prompt[:max_chars]

def save_prompt_mapping(path, prompt_list):
    with open(path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["index", "prompt"])
        for idx, prompt in enumerate(prompt_list):
            writer.writerow([idx, prompt])

def save_metadata_csv(path, metadata_list):
    with open(path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "index", "name", "genres", "duration", "director",
            "actors", "year", "description", "full_prompt"
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
                item.get("full_prompt", "")
            ])

# ========== XỬ LÝ DỮ LIỆU ==========
vectors = []
prompts = []
metadata_list = []

for doc in collection.find():
    try:
        name = doc.get("name", "").strip()
        if not name:
            continue

        genres = ', '.join(doc.get("genre", []))
        duration = str(doc.get("duration", "")).strip()
        director = doc.get("director", "").strip()
        actors = ', '.join(doc.get("actor", []))
        year = str(doc.get("year_of_release", "")).strip()
        description = doc.get("describe", "").strip()

        # Tạo prompt mô tả
        prompt = (
            f"{name} là một bộ phim thể loại {genres}"
            f"{', kéo dài ' + duration + ' phút' if duration else ''}"
            f"{', được đạo diễn bởi ' + director if director else ''}"
            f"{', với sự tham gia của ' + actors if actors else ''}"
            f"{', ra mắt vào năm ' + year if year else ''}. "
            f"{'Nội dung phim: ' + description if description else ''}"
        ).strip()
        prompt = truncate_prompt(prompt)

        vector = embed_text(prompt)

        prompts.append(prompt)
        vectors.append(vector)
        metadata_list.append({
            "name": name,
            "genres": genres,
            "duration": duration,
            "director": director,
            "actors": actors,
            "year": year,
            "description": description,
            "full_prompt": prompt
        })

    except Exception as e:
        print(f"Lỗi khi xử lý phim '{doc.get('name', 'Unknown')}': {e}")

# ========== CHUẨN HÓA & LƯU VÀO FAISS ==========
embedding_matrix = np.array(vectors).astype("float32")
embedding_matrix = l2_normalize(embedding_matrix)
index = faiss.IndexFlatL2(embedding_matrix.shape[1])
index.add(embedding_matrix)
faiss.write_index(index, INDEX_PATH)

# ========== LƯU FILE ==========
save_prompt_mapping(PROMPT_MAPPING_PATH, prompts)
save_metadata_csv(METADATA_PATH, metadata_list)

print(f"Số lượng phim đã xử lý: {len(prompts)}")
print("✅ Đã chuẩn hóa vector và lưu FAISS index, prompt mapping, metadata.")
