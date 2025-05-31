import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import csv
import unicodedata
from collections import Counter

# ========== Cấu hình ==========
VECTOR_DIR = "vector_db"
LABELS_PATH = os.path.join(VECTOR_DIR, "movie_labels.npy")
INDEX_PATH = os.path.join(VECTOR_DIR, "movie_index.faiss")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ALL_GENRES_PATH = os.path.join(VECTOR_DIR, "all_genres.csv")
ALL_ACTORS_PATH = os.path.join(VECTOR_DIR, "all_actors.csv")
ALL_DIRECTORS_PATH = os.path.join(VECTOR_DIR, "all_directors.csv")
LABEL_MAPPING_PATH = os.path.join(VECTOR_DIR, "label_mapping.csv")
similarity_threshold = 0.6

# ========== Các hàm cần thiết ==========
def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)

def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

# ========== Load từ CSV ==========
def load_keywords_from_csv(path):
    keywords = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                kw = line.strip()
                if kw:
                    keywords.add(remove_accents(kw.lower()))
    return keywords

def load_movie_labels(path):
    if os.path.exists(path):
        return np.load(path).tolist()
    return []

def load_label_mapping(path):
    mapping = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                label = int(row["label"])
                name = row["name"]
                mapping[label] = name
    return mapping

all_genres = load_keywords_from_csv(ALL_GENRES_PATH)
all_actors = load_keywords_from_csv(ALL_ACTORS_PATH)
all_directors = load_keywords_from_csv(ALL_DIRECTORS_PATH)
movie_labels = load_movie_labels(LABELS_PATH)
label_mapping = load_label_mapping(LABEL_MAPPING_PATH)  # <-- load mapping từ file CSV

# ========== Load mô hình và FAISS ==========
model = SentenceTransformer(EMBEDDING_MODEL)
index = faiss.read_index(INDEX_PATH)

# ========== Tìm phim theo keyword ==========
def search_movies_by_keyword(keyword, top_k=5):
    keyword_clean = remove_accents(keyword.strip().lower())
    query_vector = model.encode([keyword_clean])
    query_vector = l2_normalize(query_vector)
    query_vector = query_vector.astype("float32")
    distances, indices = index.search(query_vector, top_k)
    results = []

    euclidean_dist_squared = distances[0][0]
    similarity_score = 1 - euclidean_dist_squared / 2

    if similarity_score < similarity_threshold:
        return []

    for idx in indices[0]:
        if 0 <= idx < len(movie_labels):
            movie_id = movie_labels[idx]
            movie_name = label_mapping.get(movie_id, f"Phim ID {movie_id} (chưa có tên)")
            results.append(movie_name)
    return results

# ========== Lấy từ khóa trong truy vấn ==========
def extract_keywords_from_query(query):
    query_clean = remove_accents(query.lower())
    found_keywords = set()

    for kw in all_genres:
        if kw in query_clean:
            found_keywords.add(kw)
    for kw in all_actors:
        if kw in query_clean:
            found_keywords.add(kw)
    for kw in all_directors:
        if kw in query_clean:
            found_keywords.add(kw)

    return list(found_keywords)

# ========== Chương trình chính ==========
query_raw = input("🔍 Nhập nội dung mô tả phim: ").strip()
query = remove_accents(query_raw.lower())
keywords = extract_keywords_from_query(query)

if not keywords:
    print("⚠️ Không tìm thấy từ khóa phù hợp trong truy vấn.")
    print("👉 Đang thực hiện truy vấn toàn văn bằng chính mô tả bạn nhập...")

    results = search_movies_by_keyword(query_raw, top_k=1)
    if results:
        print(f"\n🎬 Phim được đề xuất gần nhất với mô tả bạn cung cấp: {results[0]}")
    else:
        print("❌ Không tìm thấy phim phù hợp với mô tả bạn nhập.")
    exit()

print(f"✅ Tìm thấy các từ khóa trong truy vấn: {keywords}")

all_found_movies = []

for kw in keywords:
    movies = search_movies_by_keyword(kw, top_k=5)
    print(f"  - Kết quả tìm kiếm với '{kw}': {movies}")
    all_found_movies.extend(movies)

counter = Counter(all_found_movies)
most_common = counter.most_common(1)

if not most_common:
    print(f"❌ Không tìm thấy phim phù hợp với truy vấn '{query_raw}'.")
    exit()

chosen_movie, count = most_common[0]
print(f"\n🎬 Phim được đề xuất nhiều nhất dựa trên các từ khóa: {chosen_movie} (xuất hiện {count} lần)")
