import os
import numpy as np
import faiss
import csv
import unicodedata
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

# ========== Cấu hình ==========
VECTOR_DIR = "vector_db"
LABELS_PATH = os.path.join(VECTOR_DIR, "movie_labels.npy")
INDEX_PATH = os.path.join(VECTOR_DIR, "movie_index.faiss")
ALL_GENRES_PATH = os.path.join(VECTOR_DIR, "all_genres.csv")
ALL_ACTORS_PATH = os.path.join(VECTOR_DIR, "all_actors.csv")
ALL_DIRECTORS_PATH = os.path.join(VECTOR_DIR, "all_directors.csv")
LABEL_MAPPING_PATH = os.path.join(VECTOR_DIR, "label_mapping.csv")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DB_NAME = "movie_database"
COLLECTION_NAME = "movies"

# ========== Chuẩn bị ==========
os.makedirs(VECTOR_DIR, exist_ok=True)
client = MongoClient("mongodb://localhost:27017/")
collection = client[DB_NAME][COLLECTION_NAME]
model = SentenceTransformer(EMBEDDING_MODEL)

def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)

def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

def embed_text(text):
    text = remove_accents(text.strip().lower())
    return model.encode(text, convert_to_numpy=True)

def save_set_to_csv(path, data_set):
    with open(path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for item in sorted(data_set):
            writer.writerow([item])

def save_dict_to_csv(path, mapping):
    with open(path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["label", "name"])
        for label, name in sorted(mapping.items()):
            writer.writerow([label, name])

# ========== Xử lý dữ liệu ==========
vectors = []
labels = []
all_genres = set()
all_actors = set()
all_directors = set()
movie_mapping = {}       # label -> name
name_to_id = {}          # name -> label
label_counter = 1

for doc in collection.find():
    try:
        name = doc.get("name", "").strip()
        if not name:
            continue

        if name not in name_to_id:
            name_to_id[name] = label_counter
            movie_mapping[label_counter] = name
            label_counter += 1

        label = name_to_id[name]

        # Genres
        for genre in doc.get("genre", []):
            genre_clean = remove_accents(genre.lower())
            all_genres.add(genre_clean)
            vectors.append(embed_text(genre))
            labels.append(label)

        # Duration
        duration = doc.get("duration")
        if duration:
            vectors.append(embed_text(str(duration)))
            labels.append(label)

        # Director
        director = doc.get("director")
        if director:
            director_clean = remove_accents(director.lower())
            all_directors.add(director_clean)
            vectors.append(embed_text(director))
            labels.append(label)

        # Actors
        for actor in doc.get("actor", []):
            actor_clean = remove_accents(actor.lower())
            all_actors.add(actor_clean)
            vectors.append(embed_text(actor))
            labels.append(label)

        # Year of release
        year = doc.get("year_of_release")
        if year:
            vectors.append(embed_text(str(year)))
            labels.append(label)

        # Description
        describe = doc.get("describe")
        if describe:
            vectors.append(embed_text(describe))
            labels.append(label)

    except Exception as e:
        print(f"Lỗi khi xử lý phim '{doc.get('name', 'Unknown')}': {e}")

# ========== Ghi FAISS index ==========
embedding_matrix = l2_normalize(np.array(vectors).astype("float32"))
labels_array = np.array(labels)
np.save(LABELS_PATH, labels_array)
index = faiss.IndexFlatL2(embedding_matrix.shape[1])
index.add(embedding_matrix)
faiss.write_index(index, INDEX_PATH)

# ========== Lưu dữ liệu ==========
save_set_to_csv(ALL_GENRES_PATH, all_genres)
save_set_to_csv(ALL_ACTORS_PATH, all_actors)
save_set_to_csv(ALL_DIRECTORS_PATH, all_directors)
save_dict_to_csv(LABEL_MAPPING_PATH, movie_mapping)

print(f"Số lượng phim: {len(movie_mapping)}")
print("✅ Đã lưu FAISS index, vectors, labels và danh sách keywords.")
