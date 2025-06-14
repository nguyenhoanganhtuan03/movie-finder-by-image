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
def create_qa_prompt(context, question, chat_history=None, previous_contexts=None):
    """
    Tạo prompt với lịch sử chat và context từ các tìm kiếm trước
    """
    history_text = ""
    if chat_history:
        history_text = "\nLỊCH SỬ CUỘC TRÒ CHUYỆN:\n"
        for i, (q, a) in enumerate(chat_history, 1):
            history_text += f"{i}. Hỏi: {q}\n   Trả lời: {a}\n"
        history_text += "\n"

    # Thêm context từ các tìm kiếm trước
    previous_context_text = ""
    if previous_contexts:
        previous_context_text = "\nTHÔNG TIN TỪ CÁC TÌM KIẾM TRƯỚC:\n"
        for i, prev_context in enumerate(previous_contexts, 1):
            previous_context_text += f"Context {i}:\n{prev_context}\n\n"

    prompt = f"""Bạn là một trợ lý AI chuyên trả lời câu hỏi về phim ảnh. Sử dụng thông tin sau đây để trả lời câu hỏi một cách chính xác và ngắn gọn.

THÔNG TIN THAM KHẢO CHO CÂU HỎI HIỆN TẠI:
{context}
{previous_context_text}{history_text}
CÂU HỎI HIỆN TẠI: {question}

HƯỚNG DẪN:
- Ưu tiên sử dụng thông tin từ "THÔNG TIN THAM KHẢO CHO CÂU HỎI HIỆN TẠI"
- Có thể tham khảo thông tin từ các tìm kiếm trước và lịch sử chat để hiểu ngữ cảnh tốt hơn
- Trả lời ngắn gọn, chính xác
- Nếu câu hỏi không có tên phim, ưu tiên tìm phim có trong LỊCH SỬ CUỘC TRÒ CHUYỆN
- Nếu không tìm thấy thông tin, nói "Tôi không tìm thấy thông tin về câu hỏi này."
- Trả lời bằng tiếng Việt

TRẢ LỜI:"""

    return prompt

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

# ========== HỆ THỐNG QA CHÍNH ==========
class MovieQASystem:
    def __init__(self, vector_db=load_vector_database(), api_key=GEMINI_API_KEY, max_history=5, max_contexts=2):
        self.db = vector_db
        self.api_key = api_key
        self.chat_history = []
        self.context_history = []
        self.max_history = max_history
        self.max_contexts = max_contexts

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
        Trả lời câu hỏi dựa trên vector database, lịch sử chat và context trước đó
        """
        # Tìm kiếm documents liên quan
        docs = self.search_relevant_docs(question)

        if not docs:
            answer = "❌ Không tìm thấy thông tin liên quan đến câu hỏi."
            current_context = ""
        else:
            # Tạo context từ các documents hiện tại
            current_context = "\n\n".join([f"- {doc.page_content}" for doc in docs])

            # Tạo prompt với lịch sử chat và context trước đó
            prompt = create_qa_prompt(
                current_context,
                question,
                self.chat_history,
                self.context_history
            )

            # Gọi Gemini API
            answer = call_gemini_api(prompt, self.api_key)

        # Lưu context hiện tại vào lịch sử context (chỉ lưu nếu có context)
        if current_context:
            self.context_history.append(current_context)

            ## Giới hạn số lượng context (chỉ giữ lại 2 context gần nhất)
            # if len(self.context_history) > self.max_contexts:
            #     self.context_history.pop(0)  

        # Lưu vào lịch sử chat
        self.chat_history.append((question, answer))

        # Giới hạn số lượng lịch sử chat
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)  

        return answer

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
    print("🎬 HỆ THỐNG TRẢ LỜI CÂU HỎI VỀ PHIM ẢNH (Với Context Memory)")
    print("=" * 60)

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