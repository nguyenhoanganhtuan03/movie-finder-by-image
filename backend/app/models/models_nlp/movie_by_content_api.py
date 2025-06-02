import os
import requests
import csv
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import faiss

# ==== CẤU HÌNH ====
load_dotenv()
VECTOR_DIR = "vector_db"
INDEX_PATH = os.path.join(VECTOR_DIR, "index_movie.faiss")
PROMPT_MAPPING_PATH = os.path.join(VECTOR_DIR, "prompt_mapping.csv")
SIMILARITY_THRESHOLD = 0.3
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
METADATA_PATH = os.path.join(VECTOR_DIR, "metadata.csv")

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
2. TÌM KIẾM thông tin phim từ dữ liệu được cung cấp
3. TRÍCH XUẤT các thông tin chính của phim
4. TRẢ VỀ kết quả theo định dạng yêu cầu

CÂU HỎI NGƯỜI DÙNG: "{user_query}"

NHIỆM VỤ:
- Từ câu hỏi, hãy xác định các keywords chính trong câu hỏi
- Trích xuất các thông tin: thể loại, thời lượng, đạo diễn, diễn viên, năm ra mắt, nội dung

YÊU CẦU ĐỊNH DẠNG TRẢ LỜI:
Trả lời chính xác theo mẫu sau (thay thế các phần trong ngoặc nhọn):

"Một bộ phim thể loại {{genre}}, kéo dài {{duration}} phút, được đạo diễn bởi {{director}}, với sự tham gia của {{actor}}, ra mắt vào năm {{year}}. Nội dung phim: {{description}}"

LưU Ý:
- Nếu không tìm thấy thông tin nào, hãy bỏ qua thông tin đó trong câu mẫu.
- Chỉ sử dụng thông tin có trong câu hỏi người dùng.
Ví dụ:
    - CÂU HỎI NGƯỜI DÙNG: phim kinh dị có Việt Hương đóng
    - TRẢ LỜI: Một bộ phim thể loại kinh dị, với sự tham gia của Việt Hương.

TRẢ LỜI:"""

    return call_gemini_api(prompt)

# ========== HÀM PHÂN TÍCH CÂU HỎI ==========
def search_movies_by_user_query(user_query, top_k=5):
    # 1. Sinh prompt truy vấn từ Gemini
    search_prompt = create_keyword_analysis_prompt(user_query)

    # 2. Embed và tìm trong FAISS
    query_vec = l2_normalize(embed_text(search_prompt).astype('float32'))
    distances, indices = index.search(query_vec, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        similarity = 1 - dist / 2
        if similarity >= SIMILARITY_THRESHOLD:
            movie_name = metadata_mapping.get(idx, f"Phim có ID {idx}")
            results.append((movie_name, similarity))

    return search_prompt, results

# ========== MAIN ==========
while True:
    user_input = input("Nhập câu hỏi của bạn (hoặc 'quit' để thoát): ").strip()
    if user_input.lower() == "quit":
        print("👋 Thoát chương trình.")
        break

    prompt, movies = search_movies_by_user_query(user_input)

    print("\n🧠 Prompt dùng để truy vấn:", prompt)
    if movies:
        print("🎬 Kết quả tìm được:")
        for name, score in movies:
            print(f"- {name} (độ tương đồng: {score:.2f})")
    else:
        print("❌ Không tìm thấy phim phù hợp.\n")
