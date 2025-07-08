import os
import requests
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain.prompts import PromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain.schema import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.language_models.chat_models import SimpleChatModel

# ==== CẤU HÌNH ====
load_dotenv()
base_dir = os.path.dirname(os.path.abspath(__file__))
MOVIE_VECTOR_DB = os.path.join(base_dir, "vector_db/movie_vector_db")
EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_3")
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
    headers = {"Content-Type": "application/json"}
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

# ========== PROMPT TEMPLATE ==========
def create_qa_prompt():
    return (
        "Bạn là một chuyên gia điện ảnh. Trả lời câu hỏi của người dùng về các bộ phim, "
        "diễn viên, đạo diễn, thể loại hoặc năm phát hành một cách chính xác và dễ hiểu."
    )

prompt = PromptTemplate(
    input_variables=["history", "input"],
    template="""
Bạn là một trợ lý AI chuyên về phim ảnh. Dựa vào lịch sử hội thoại và câu hỏi mới, hãy trả lời ngắn gọn và đúng trọng tâm.

Lịch sử hội thoại:
{history}

Câu hỏi: {input}
Trợ lý:"""
)

# ========== GEMINI CHAT MODEL WRAPPER ==========
class GeminiChatModel(SimpleChatModel):
    @property
    def _llm_type(self) -> str:
        return "gemini-chat-model"

    def _call(self, messages, **kwargs):
        parts = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                parts.append({"role": "user", "parts": [{"text": msg.content}]})
            elif isinstance(msg, AIMessage):
                parts.append({"role": "model", "parts": [{"text": msg.content}]})

        # ✨ Không cần nhồi prompt nếu đã có lịch sử
        if not parts:
            # Nếu lần đầu tiên, mới nhét prompt
            parts.append({"role": "user", "parts": [{"text": create_qa_prompt()}]})

        # Gọi Gemini API
        response = call_gemini_api_conversational(parts, GEMINI_API_KEY)
        return response

# ========== HỆ THỐNG QA ==========
class MovieQASystem:
    def __init__(self, vector_db=None, api_key=None):
        self.db = vector_db or load_vector_database()
        self.api_key = api_key or GEMINI_API_KEY

        llm = GeminiChatModel()

        llm_chain = RunnableLambda(
            lambda inputs: GeminiChatModel()._call(inputs["history"] + [HumanMessage(content=inputs["input"])])
        )

        self.chain = RunnableWithMessageHistory(
            llm_chain,
            lambda session_id: InMemoryChatMessageHistory(),
            input_messages_key="input",
            history_messages_key="history",
        )

    def search_relevant_docs(self, query, k=10):
        try:
            return self.db.similarity_search(query, k=k)
        except Exception as e:
            print(f"❌ Lỗi khi tìm kiếm: {e}")
            return []

    def answer_question(self, question):
        docs = self.search_relevant_docs(question)
        context = "\n".join(f"- {doc.page_content}" for doc in docs) if docs else ""
        if context:
            question = f"THÔNG TIN THAM KHẢO:\n{context}\n\nCÂU HỎI: {question}"

        result = self.chain.invoke(
            {"input": question},
            config={"configurable": {"session_id": "movie_qa_session"}}
        )
        return result.content if hasattr(result, "content") else result

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
def main():
    print("\U0001f3ac HỆ THỐNG TRẢ LỜI CÂU HỎI VỀ PHIM ẢNH (Với Context Memory)")
    print("=" * 60)
    if not GEMINI_API_KEY:
        print("❌ Vui lòng đặt biến môi trường GEMINI_API_KEY.")
        return
    print("🔄 Đang load vector database...")
    try:
        db = load_vector_database()
        print("✅ Load vector database thành công!")
    except Exception as e:
        print(f"❌ {e}")
        return
    qa_system = MovieQASystem(db, GEMINI_API_KEY)
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
