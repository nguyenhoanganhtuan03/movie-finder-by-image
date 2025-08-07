import os
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import re
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

# ==== WRAPPER EMBEDDING CHO LANGCHAIN ====
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


# ==== HÀM GỌI GEMINI API (có duy trì lịch sử) ====
def call_gemini_api_with_history(message_history, api_key):
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": message_history,
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


# ==== PROMPT KHỞI TẠO ====
def create_qa_prompt():
    return (
        "Bạn là một chuyên gia điện ảnh. Trả lời câu hỏi của người dùng về các bộ phim, "
        "Trả lời ngắn gọn, dễ hiểu."
        "Hãy duy trì ngữ cảnh của cuộc trò chuyện và tham khảo các câu hỏi trước đó khi cần thiết. "
        "Nếu người dùng hỏi về 'phim này', 'bộ phim đó', 'phim vừa nói', hoặc không đề cập tên phim. Hãy hiểu họ đang nhắc đến phim được đề cập gần nhất."
    )


# ==== HỆ THỐNG QA ====
class MovieQASystem:
    def __init__(self, vector_db=None, api_key=None, max_history=10):
        self.db = vector_db or load_vector_database()
        self.api_key = api_key or GEMINI_API_KEY
        self.max_history = max_history

        # Khởi tạo lịch sử với system prompt
        self.message_history = [
            {"role": "user", "parts": [{"text": create_qa_prompt()}]},
            {"role": "model", "parts": [{
                        "text": "Chào bạn! Tôi là chuyên gia điện ảnh. Tôi sẽ trả lời các câu hỏi về phim. Hãy hỏi tôi bất kỳ điều gì về phim nhé!"}]}
        ]

        self.last_used_docs = []
        self.current_movie_context = None

    def search_relevant_docs(self, query, k=20):
        try:
            return self.db.similarity_search(query, k=k)
        except Exception as e:
            print(f"❌ Lỗi khi tìm kiếm: {e}")
            return []

    def update_history(self, role, text):
        """Cập nhật lịch sử trò chuyện"""
        self.message_history.append({"role": role, "parts": [{"text": text}]})

        # Giữ lại system prompt và giới hạn lịch sử
        if len(self.message_history) > self.max_history + 2:  # +2 cho system prompt và response
            # Giữ lại system prompt (2 message đầu) và các message gần nhất
            system_messages = self.message_history[:2]
            recent_messages = self.message_history[-(self.max_history):]
            self.message_history = system_messages + recent_messages

    def extract_movie_from_response(self, response):
        """Trích xuất tên phim từ câu trả lời để lưu context"""
        # Tìm kiếm pattern phim trong câu trả lời
        movie_patterns = [
            r'[Pp]him\s+["\*]?([^"\*\n]+)["\*]?',
            r'[Bb]ộ phim\s+["\*]?([^"\*\n]+)["\*]?',
            r'[Tt]ác phẩm\s+["\*]?([^"\*\n]+)["\*]?'
        ]

        for pattern in movie_patterns:
            matches = re.findall(pattern, response)
            if matches:
                return matches[0].strip()
        return None

    def build_context_aware_prompt(self, question, docs):
        """Tạo prompt có nhận thức về ngữ cảnh"""
        context_parts = []

        # Thêm thông tin từ vector database
        if docs:
            doc_context = "\n".join(f"- {doc.page_content}" for doc in docs)
            context_parts.append(f"THÔNG TIN THAM KHẢO:\n{doc_context}")

        # Thêm ngữ cảnh phim hiện tại nếu có
        if self.current_movie_context:
            context_parts.append(f"PHIM ĐANG THẢO LUẬN: {self.current_movie_context}")

        # Thêm lời nhắc về ngữ cảnh
        context_parts.append(
            "LƯU Ý: Hãy tham khảo các câu hỏi và câu trả lời trước đó trong cuộc trò chuyện để hiểu đúng ngữ cảnh.")

        if context_parts:
            full_context = "\n\n".join(context_parts)
            return f"{full_context}\n\nCÂU HỎI: {question}"
        else:
            return f"CÂU HỎI: {question}"

    def is_context_dependent_question(self, question):
        """Kiểm tra xem câu hỏi có phụ thuộc vào ngữ cảnh không"""
        context_indicators = [
            'phim này', 'phim đó', 'phim vừa nói', 'bộ phim này', 'bộ phim đó',
            'phim trên', 'phim nói ở trên', 'có những ai', 'diễn viên nào',
            'khi nào', 'năm nào', 'thể loại gì', 'đạo diễn nào'
        ]

        question_lower = question.lower()
        return any(indicator in question_lower for indicator in context_indicators)

    def answer_question(self, question):
        """Trả lời câu hỏi với duy trì ngữ cảnh"""
        # Tìm kiếm documents liên quan
        docs = self.search_relevant_docs(question)

        # Nếu không tìm thấy doc mới và câu hỏi phụ thuộc ngữ cảnh, dùng doc cũ
        if not docs and self.is_context_dependent_question(question):
            docs = self.last_used_docs

        # Cập nhật doc được sử dụng
        if docs:
            self.last_used_docs = docs

        # Tạo prompt có nhận thức ngữ cảnh
        prompt = self.build_context_aware_prompt(question, docs)

        # Thêm câu hỏi vào lịch sử
        self.update_history("user", prompt)

        # Gọi API
        response = call_gemini_api_with_history(self.message_history, self.api_key)

        # Cập nhật ngữ cảnh phim hiện tại
        movie_mentioned = self.extract_movie_from_response(response)
        if movie_mentioned:
            self.current_movie_context = movie_mentioned

        # Thêm câu trả lời vào lịch sử
        self.update_history("model", response)

        return response

# ========== ĐỌC VECTORSTORE FAISS ==========
def load_vector_database():
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
qa_system = None

def initialize_qa_system():
    global qa_system
    if qa_system is None:
        db = load_vector_database()
        qa_system = MovieQASystem(db, GEMINI_API_KEY)
    return qa_system

def process_user_question(question: str) -> str:
    qa = initialize_qa_system()
    return qa.answer_question(question.strip())

def main():
    print("🎬 HỆ THỐNG TRẢ LỜI CÂU HỎI VỀ PHIM ẢNH (Với Context Memory)")
    print("=" * 60)
    
    if not GEMINI_API_KEY:
        print("❌ Vui lòng đặt biến môi trường GEMINI_API_KEY.")
        return

    print("🔄 Đang load vector database...")
    try:
        initialize_qa_system()
        print("✅ Load vector database thành công!")
    except Exception as e:
        print(f"❌ {e}")
        return

    print("\n🤖 Hệ thống đã sẵn sàng! Hãy đặt câu hỏi về phim ảnh.")
    print("   - 'quit' hoặc 'exit': Thoát chương trình")
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
            answer = process_user_question(question)
            print(f"\n🤖 Trả lời:\n{answer}")
            print("-" * 50)
        except KeyboardInterrupt:
            print("\n👋 Đã dừng chương trình.")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            continue

if __name__ == "__main__":
    main()
