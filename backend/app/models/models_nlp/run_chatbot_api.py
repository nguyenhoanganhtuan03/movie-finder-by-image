import os
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings

# ==== CẤU HÌNH ====
load_dotenv()
base_dir = os.path.dirname(os.path.abspath(__file__))
MOVIE_VECTOR_DB = os.path.join(base_dir, "vector_db/movie_vector_db")
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# ==== LOAD MODEL EMBEDDING ====
model = SentenceTransformer(EMBEDDING_MODEL)
model.max_seq_length = 2048


# ========== WRAPPER EMBEDDING CHO LANGCHAIN ==========
class SentenceTransformerEmbeddingWrapper(Embeddings):
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text):
        embedding = self.model.encode([text], convert_to_numpy=True)[0]
        return embedding.tolist()


embedding_wrapper = SentenceTransformerEmbeddingWrapper(model)

# ========== HÀM GỌI GEMINI API ==========
def call_gemini_api_conversational(messages, api_key):
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": messages,
        "generationConfig": {
            "temperature": 0.7,
            "topK": 10,
            "topP": 0.95,
            "maxOutputTokens": 2048,
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
            candidates = result.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
            return "❌ Không nhận được phản hồi từ Gemini API."
        return f"❌ Lỗi API Gemini: {response.status_code} - {response.text}"

    except Exception as e:
        return f"❌ Lỗi khi gọi Gemini: {str(e)}"

# ========== TẠO PROMPT TEMPLATE ==========
def create_qa_prompt():

    prompt = f"""
                    "Bạn là một trợ lý AI chuyên trả lời câu hỏi về phim ảnh bằng tiếng Việt. "
                    "Sử dụng thông tin bên dưới để trả lời."
                    "Trả lời chính xác và ngắn gọn. Nếu không rõ, hãy nói 'Tôi không biết.'"
            """

    return prompt

# ========== HỆ THỐNG QA CHÍNH ==========
class MovieQASystem:
    def __init__(self, vector_db=None, api_key=None, max_history=10):
        self.db = vector_db or load_vector_database()
        self.api_key = api_key or GEMINI_API_KEY
        self.max_history = max_history
        self.message_history = [
            {
                "role": "user",
                "parts": [{"text": (create_qa_prompt())}]
            }
        ]

    def search_relevant_docs(self, query, k=20):
        try:
            return self.db.similarity_search(query, k=k)
        except Exception as e:
            print(f"❌ Lỗi khi tìm kiếm: {e}")
            return []

    def answer_question(self, question):
        # Tìm context từ FAISS
        docs = self.search_relevant_docs(question)
        context = "\n".join(f"- {doc.page_content}" for doc in docs) if docs else ""

        # Gộp context (nếu có) vào câu hỏi mới
        if context:
            user_message = f"THÔNG TIN THAM KHẢO:\n{context}\n\nCÂU HỎI: {question}"
        else:
            user_message = question

        # Thêm câu hỏi mới vào message history
        self.message_history.append({"role": "user", "parts": [{"text": user_message}]})

        # Gọi Gemini
        answer = call_gemini_api_conversational(self.message_history, self.api_key)

        # Thêm câu trả lời vào message history
        self.message_history.append({"role": "model", "parts": [{"text": answer}]})

        # Cắt bớt nếu quá dài
        if len(self.message_history) > self.max_history * 2 + 1:
            self.message_history = [self.message_history[0]] + self.message_history[-(self.max_history * 2):]

        return answer
    
# ========== ĐỌC VECTORSTORE FAISS ==========
def load_vector_database():
    """
    Load FAISS vector database
    """
    if not os.path.exists(MOVIE_VECTOR_DB):
        raise FileNotFoundError(f"Thư mục vector DB không tồn tại: {MOVIE_VECTOR_DB}")

    try:
        db = FAISS.load_local(
            MOVIE_VECTOR_DB,
            embedding_wrapper,
            allow_dangerous_deserialization=True
        )
        return db
    except Exception as e:
        raise Exception(f"Lỗi khi load vector database: {e}")

# ========== MAIN PROGRAM ==========
def main():
    print("🎬 HỆ THỐNG TRẢ LỜI CÂU HỎI VỀ PHIM ẢNH (Với Context Memory)")
    print("=" * 60)

    # Kiểm tra API key
    if not GEMINI_API_KEY:
        print("❌ Vui lòng đặt biến môi trường GEMINI_API_KEY.")
        print("Ví dụ: export GEMINI_API_KEY='your_api_key_here'")
        return

    # Load vector database
    print("🔄 Đang load vector database...")
    try:
        db = load_vector_database()
        print("✅ Load vector database thành công!")
    except Exception as e:
        print(f"❌ {e}")
        return

    # Khởi tạo hệ thống QA
    qa_system = MovieQASystem(db, GEMINI_API_KEY)

    print("\n🤖 Hệ thống đã sẵn sàng! Hãy đặt câu hỏi về phim ảnh.")
    print("   - 'quit' hoặc 'exit': Thoát chương trình")

    # Vòng lặp chính
    while True:
        try:
            question = input("❓ Câu hỏi của bạn: ").strip()

            if question.lower() in ['quit', 'exit', 'thoát']:
                print("👋 Cảm ơn bạn đã sử dụng hệ thống!")
                break

            if not question:
                print("⚠️ Vui lòng nhập câu hỏi.")
                continue

            print("🔄 Đang tìm kiếm và tạo câu trả lời...")

            # Trả lời câu hỏi
            answer = qa_system.answer_question(question)

            print(f"\n🤖 Trả lời:")
            print(f"{answer}")
            print("-" * 50)

        except KeyboardInterrupt:
            print("\n👋 Đã dừng chương trình.")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            continue


# if __name__ == "__main__":
#     main()