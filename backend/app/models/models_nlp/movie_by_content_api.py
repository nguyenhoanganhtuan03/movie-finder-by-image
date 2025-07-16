import os
import requests
import csv
import numpy as np
from collections import Counter, defaultdict
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import faiss

# ==== CẤU HÌNH ====
load_dotenv()
base_dir = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(base_dir, "vector_db/index_movie.faiss")
LABELS_MAPPING_PATH = os.path.join(base_dir, "vector_db/labels_mapping.csv")
# SIMILARITY_THRESHOLD = 0.8
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
METADATA_PATH = os.path.join(base_dir, "vector_db/metadata.csv")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_2")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# ==== LOAD MODEL EMBEDDING và FAISS ====
model = SentenceTransformer(EMBEDDING_MODEL)
model.max_seq_length = 2048
index = faiss.read_index(INDEX_PATH)

# ========== HÀM TIỆN ÍCH ==========
def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)

def embed_text(text):
    text = text.strip().lower()
    return model.encode([text], convert_to_numpy=True)

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

def load_labels_mapping(path):
    mapping = {}
    with open(path, encoding='utf-8') as f:
        next(f)  # Bỏ dòng tiêu đề
        for line in f:
            index, name = line.strip().split(',', 1)
            mapping[int(index)] = name
    return mapping

labels_mapping = load_labels_mapping(LABELS_MAPPING_PATH)

# ========== HÀM GỌI GEMINI API ==========
def call_gemini_api(prompt, api_key=GEMINI_API_KEY):
    """
    Gọi Gemini API để tạo câu trả lời
    """
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.01,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024,
        }
    }

    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                return content.strip()
            else:
                return "❌ Không nhận được phản hồi từ Gemini API."
        else:
            return f"❌ Lỗi API Gemini: {response.status_code} - {response.text}"

    except requests.exceptions.Timeout:
        return "❌ Timeout khi gọi Gemini API."
    except requests.exceptions.RequestException as e:
        return f"❌ Lỗi kết nối: {str(e)}"
    except Exception as e:
        return f"❌ Lỗi không xác định: {str(e)}"


# ========== PHÂN TÍCH KEYWORD VÀ TẠO PROMPT ==========
def create_keyword_analysis_prompt(user_query):
    """
    Tạo prompt để Gemini phân tích keyword và trích xuất thông tin phim
    """
    prompt = f"""Bạn là một chuyên gia phân tích thông tin phim ảnh. Nhiệm vụ của bạn là:

1. PHÂN TÍCH câu hỏi của người dùng để tìm tên phim
2. TRẢ VỀ kết quả theo định dạng yêu cầu

CÂU HỎI NGƯỜI DÙNG: "{user_query}"

NHIỆM VỤ:
- Từ câu hỏi, hãy xác định các keywords chính trong câu hỏi
- Trích xuất các thông tin: thể loại, thời lượng, đạo diễn, diễn viên, năm ra mắt, nội dung

YÊU CẦU ĐỊNH DẠNG TRẢ LỜI: các từ khóa chính, ngăn cách bằng dấu phẩy

LưU Ý:
- Chỉ sử dụng thông tin có trong câu hỏi người dùng.
Ví dụ:
    - CÂU HỎI NGƯỜI DÙNG: phim kinh dị, hài, có Trấn Thành đóng, lấy bối cảnh bệnh viện
    - TRẢ LỜI: kinh dị, hài, Trấn Thành, bệnh viện

TRẢ LỜI:"""

    return call_gemini_api(prompt)

# ========== HÀM PHÂN TÍCH CÂU HỎI ==========
def search_movies_by_user_query(user_query, SIMILARITY_THRESHOLD, n_movies):
    search_prompt = create_keyword_analysis_prompt(user_query)
    keywords = [kw.strip().lower() for kw in search_prompt.split(",") if kw.strip()]

    movie_stats = defaultdict(lambda: {"count": 0, "min_distance": float("inf")})

    for keyword in keywords:
        query_vec = l2_normalize(embed_text(keyword).astype('float32')).reshape(1, -1)
        distances, indices = index.search(query_vec, n_movies*2)

        for dist, idx in zip(distances[0], indices[0]):
            similarity = 1 - dist / 2
            if similarity >= SIMILARITY_THRESHOLD:
                movie_name = labels_mapping.get(idx, f"Phim có ID {idx}")
                movie_stats[movie_name]["count"] += 1
                movie_stats[movie_name]["min_distance"] = min(movie_stats[movie_name]["min_distance"], dist)

    sorted_movies = sorted(
        movie_stats.items(),
        key=lambda x: (-x[1]["count"], x[1]["min_distance"])
    )

    # Tách phim xuất hiện nhiều nhất (ưu tiên vector gần hơn khi bằng nhau)
    top_n_movies = [(name, stats["count"]) for name, stats in sorted_movies[:n_movies]]

    # Tất cả phim phù hợp 
    all_matched_movies = [(name, stats["count"]) for name, stats in sorted_movies]

    print(f"Từ khóa: {search_prompt}")
    print(all_matched_movies)

    return search_prompt, top_n_movies, all_matched_movies

# ========== MAIN ==========
while True:
    user_input = input("Nhập câu hỏi của bạn (hoặc 'quit' để thoát): ").strip()
    if user_input.lower() == "quit":
        print("👋 Thoát chương trình.")
        break

    prompt, top_movies, all_matched_movies = search_movies_by_user_query(user_input, 0.8, 5)
    name_movies = [name for name, _ in top_movies]
    print(name_movies)

    print("\n🧠 Prompt dùng để truy vấn:", prompt)
    if top_movies:
        print("🎬 Kết quả tìm được:")
        for name, score in top_movies:
            print(f"- {name}")
    else:
        print("❌ Không tìm thấy phim phù hợp.\n")
