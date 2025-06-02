import os
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings

# ==== CẤU HÌNH ====
load_dotenv()
VECTOR_DIR = "vector_db/movie_vector_db"
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# ==== LOAD MODEL EMBEDDING ====
model = SentenceTransformer(EMBEDDING_MODEL)


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
def call_gemini_api(prompt, api_key):
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
            "temperature": 0.7,
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


# ========== TẠO PROMPT TEMPLATE ==========
def create_qa_prompt(context, question, chat_history=None):
    """
    Tạo prompt với lịch sử chat (nếu có)
    """
    history_text = ""
    if chat_history:
        history_text = "\nLỊCH SỬ CUỘC TRÒ CHUYỆN:\n"
        for i, (q, a) in enumerate(chat_history, 1):
            history_text += f"{i}. Hỏi: {q}\n   Trả lời: {a}\n"
        history_text += "\n"

    prompt = f"""Bạn là một trợ lý AI chuyên trả lời câu hỏi về phim ảnh. Sử dụng thông tin sau đây để trả lời câu hỏi một cách chính xác và ngắn gọn.

THÔNG TIN THAM KHẢO:
{context}
{history_text}
CÂU HỎI HIỆN TẠI: {question}

HƯỚNG DẪN:
- Ưu tiên sử dụng thông tin từ "THÔNG TIN THAM KHẢO"
- Có thể tham khảo lịch sử chat để hiểu ngữ cảnh
- Trả lời ngắn gọn, chính xác
- Nếu câu hỏi liên quan đến câu hỏi trước, hãy liên kết thông tin
- Nếu không tìm thấy thông tin, nói "Tôi không tìm thấy thông tin về câu hỏi này."
- Trả lời bằng tiếng Việt

TRẢ LỜI:"""

    return prompt


# ========== HỆ THỐNG QA CHÍNH ==========
class MovieQASystem:
    def __init__(self, vector_db, api_key, max_history=5):
        self.db = vector_db
        self.api_key = api_key
        self.chat_history = []  # Lưu lịch sử chat
        self.max_history = max_history  # Giới hạn số câu hỏi lưu

    def search_relevant_docs(self, question, k=3):
        """
        Tìm kiếm các document liên quan đến câu hỏi
        """
        try:
            docs = self.db.similarity_search(question, k=k)
            return docs
        except Exception as e:
            print(f"❌ Lỗi khi tìm kiếm: {e}")
            return []

    def answer_question(self, question):
        """
        Trả lời câu hỏi dựa trên vector database và lịch sử chat
        """
        # Tìm kiếm documents liên quan
        docs = self.search_relevant_docs(question)

        if not docs:
            answer = "❌ Không tìm thấy thông tin liên quan đến câu hỏi."
        else:
            # Tạo context từ các documents
            context = "\n\n".join([f"- {doc.page_content}" for doc in docs])

            # Tạo prompt với lịch sử chat
            prompt = create_qa_prompt(context, question, self.chat_history)

            # Gọi Gemini API
            answer = call_gemini_api(prompt, self.api_key)

        # Lưu vào lịch sử chat
        self.chat_history.append((question, answer))

        # Giới hạn số lượng lịch sử
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)  # Xóa câu hỏi cũ nhất

        return answer

    def clear_history(self):
        """Xóa lịch sử chat"""
        self.chat_history.clear()
        return "✅ Đã xóa lịch sử cuộc trò chuyện."

    def show_history(self):
        """Hiển thị lịch sử chat"""
        if not self.chat_history:
            return "📝 Chưa có lịch sử cuộc trò chuyện."

        history_text = "📝 LỊCH SỬ CUỘC TRÒ CHUYỆN:\n" + "=" * 40 + "\n"
        for i, (q, a) in enumerate(self.chat_history, 1):
            history_text += f"{i}. ❓ {q}\n   🤖 {a}\n" + "-" * 40 + "\n"
        return history_text


# ========== ĐỌC VECTORSTORE FAISS ==========
def load_vector_database():
    """
    Load FAISS vector database
    """
    if not os.path.exists(VECTOR_DIR):
        raise FileNotFoundError(f"Thư mục vector DB không tồn tại: {VECTOR_DIR}")

    try:
        db = FAISS.load_local(
            VECTOR_DIR,
            embedding_wrapper,
            allow_dangerous_deserialization=True
        )
        return db
    except Exception as e:
        raise Exception(f"Lỗi khi load vector database: {e}")


# ========== TEST API CONNECTION ==========
def test_gemini_connection(api_key):
    """
    Test kết nối với Gemini API
    """
    test_prompt = "Xin chào, bạn có thể trả lời câu hỏi này không?"
    response = call_gemini_api(test_prompt, api_key)

    if "❌" not in response:
        print("✅ Kết nối Gemini API thành công!")
        return True
    else:
        print(f"❌ Lỗi kết nối Gemini API: {response}")
        return False


# ========== MAIN PROGRAM ==========
def main():
    print("🎬 HỆ THỐNG TRẢ LỜI CÂU HỎI VỀ PHIM ẢNH")
    print("=" * 50)

    # Kiểm tra API key
    if not GEMINI_API_KEY:
        print("❌ Vui lòng đặt biến môi trường GEMINI_API_KEY.")
        print("Ví dụ: export GEMINI_API_KEY='your_api_key_here'")
        return

    # Test kết nối API
    print("🔄 Đang kiểm tra kết nối Gemini API...")
    if not test_gemini_connection(GEMINI_API_KEY):
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
    print("💡 Lệnh đặc biệt:")
    print("   - 'quit' hoặc 'exit': Thoát chương trình")
    print("   - 'history': Xem lịch sử chat")
    print("   - 'clear': Xóa lịch sử chat\n")

    # Vòng lặp chính
    while True:
        try:
            question = input("❓ Câu hỏi của bạn: ").strip()

            if question.lower() in ['quit', 'exit', 'thoát']:
                print("👋 Cảm ơn bạn đã sử dụng hệ thống!")
                break

            # Lệnh xem lịch sử
            if question.lower() in ['history', 'lịch sử']:
                print(qa_system.show_history())
                continue

            # Lệnh xóa lịch sử
            if question.lower() in ['clear', 'xóa']:
                print(qa_system.clear_history())
                continue

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


if __name__ == "__main__":
    main()