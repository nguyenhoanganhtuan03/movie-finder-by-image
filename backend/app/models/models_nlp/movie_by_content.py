import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from collections import Counter

from langchain_community.llms import CTransformers
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# ========== Cấu hình ==========
VECTOR_PATH = "vector_db/vector_similarity.faiss"
METADATA_PATH = "vector_db/movie_metadata.json"
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
GGUF_MODEL_PATH = "models_llm/vinallama-7b-chat_q5_0.gguf"
similarity_threshold = 0.4
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ========== Load model nhúng ==========
model = SentenceTransformer(EMBEDDING_MODEL)
model.max_seq_length = 2048

# ========== Chuẩn hóa vector ==========
def l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / (norms + 1e-10)

# ========== Load FAISS & metadata ==========
if not os.path.exists(VECTOR_PATH) or not os.path.exists(METADATA_PATH):
    raise FileNotFoundError("❌ FAISS index hoặc metadata chưa tồn tại.")

index = faiss.read_index(VECTOR_PATH)
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

# ========== Load mô hình PhoGPT ==========
if not os.path.exists(GGUF_MODEL_PATH):
    raise FileNotFoundError("❌ PhoGPT model chưa được cài đặt.")

llm = CTransformers(
    model=GGUF_MODEL_PATH,
    model_type="llama",
    config={"max_new_tokens": 512, "temperature": 0.01}
)

# ========== Tạo prompt phân tích ==========
prompt_template = PromptTemplate(
    input_variables=["query"],
    template="""
        Bạn là trợ lý AI. Hãy phân tích mô tả sau và tách nó thành các phần cụ thể như:
        - Diễn viên:
        - Thể loại:
        - Đạo diễn:
        - Nội dung:
        - Năm phát hành (nếu có):
        
        Nếu không có phần nào, hãy để trống phần đó.
        
        Mô tả: "{query}"
        ---
        """
    )

chain = LLMChain(prompt=prompt_template, llm=llm)

# ========== Nhận truy vấn người dùng ==========
query = input("🔍 Nhập nội dung mô tả phim: ").strip()
structured_info = chain.run(query)

print("\n📋 Truy vấn đã phân tích:\n", structured_info)

# ========== Chuyển truy vấn phân tích thành văn bản chuẩn để nhúng ==========
def convert_to_clean_text(info_str):
    lines = info_str.strip().splitlines()
    final_text = ""
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            final_text += f"{key.strip().capitalize()}: {value.strip()}. "
    return final_text.strip()

processed_query = convert_to_clean_text(structured_info)
query_vector = l2_normalize(model.encode([processed_query]).astype("float32"))
D, I = index.search(query_vector, k=5)

# ========== Tính điểm tương đồng ==========
euclidean_dist_squared = D[0][0]
similarity_score = 1 - euclidean_dist_squared / 2

if similarity_score < similarity_threshold:
    print("Threshold:", similarity_score)
    print(f"❌ Không tìm thấy phim nào phù hợp với truy vấn '{query}'.")
    exit()

# ========== Xử lý kết quả ==========
names = [metadata[idx]["movie_name"] for idx in I[0]]
counter = Counter(names)
most_common = counter.most_common(1)[0]

if most_common[1] >= (len(names) / 2):
    chosen_movie = most_common[0]
else:
    chosen_movie = names[0]

print("Threshold:", similarity_score)
print(f"🎬 Phim được đề xuất: {chosen_movie}")
