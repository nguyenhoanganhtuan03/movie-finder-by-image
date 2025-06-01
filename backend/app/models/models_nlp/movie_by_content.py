import os
import numpy as np
import faiss
import csv
from sentence_transformers import SentenceTransformer
from pyvi.ViTokenizer import tokenize

# ========== Cấu hình ==========
VECTOR_DIR = "vector_db"
INDEX_PATH = os.path.join(VECTOR_DIR, "index_movie.faiss")
PROMPT_MAPPING_PATH = os.path.join(VECTOR_DIR, "prompt_mapping.csv")
SIMILARITY_THRESHOLD = 0.3
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
# EMBEDDING_MODEL = "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
METADATA_PATH = os.path.join(VECTOR_DIR, "metadata.csv")

# ========== Load mô hình và FAISS ==========
model = SentenceTransformer(EMBEDDING_MODEL)
model.max_seq_length = 2048
index = faiss.read_index(INDEX_PATH)

# ========== Hàm tiện ích ==========
def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)

# def embed_text(text):
#     text = text.strip().lower()
#     tokenized = tokenize(text)
#     embedding = model.encode([tokenized], convert_to_numpy=True)
#     return l2_normalize(embedding)

def embed_text(text):
    text = text.strip().lower()
    return model.encode([text], convert_to_numpy=True)

# ========== Load metadata ==========
def load_metadata(path):
    metadata = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                idx = int(row['index'])
                name = row.get('name', f"Phim có ID {idx}")
                metadata[idx] = name
    return metadata

metadata_mapping = load_metadata(METADATA_PATH)

# ========== Load prompt mapping ==========
def load_prompt_mapping(path):
    mapping = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            next(f)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",", 1)
                if len(parts) != 2:
                    # print(f"Bỏ qua dòng không hợp lệ: {line}")
                    continue
                idx, prompt = parts
                try:
                    mapping[int(idx)] = prompt
                except ValueError:
                    # print(f"Bỏ qua dòng có index không phải số: {line}")
                    pass
    return mapping

prompt_mapping = load_prompt_mapping(PROMPT_MAPPING_PATH)

# ========== Hàm tìm phim tương tự ==========
def find_similar_movies(query, top_k=5):
    query_vec = l2_normalize(embed_text(query).astype('float32'))
    distances, indices = index.search(query_vec, top_k)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        similarity = 1 - dist / 2
        if similarity >= SIMILARITY_THRESHOLD:
            movie_name = metadata_mapping.get(idx, f"Phim có ID {idx}")
            results.append((movie_name, similarity))
    return results

# ========== Main ==========
if __name__ == "__main__":
    while True:
        user_query = input("🔍 Nhập mô tả phim bạn muốn tìm (hoặc gõ 'quit' để thoát): ").strip()
        if user_query.lower() == "quit":
            print("👋 Kết thúc chương trình.")
            break

        matches = find_similar_movies(user_query, top_k=5)

        if not matches:
            print("❌ Không tìm thấy phim phù hợp với mô tả của bạn.")
        else:
            print("\n🎬 Các phim gần nhất với mô tả của bạn:")
            for i, (movie_prompt, score) in enumerate(matches, 1):
                print(f"{i}. {movie_prompt} (độ tương đồng: {score:.3f})")
