import os
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# ========== CẤU HÌNH ==========
VECTOR_DIR = "vector_db/movie_vector_db"
EMBEDDING_MODEL_NAME = "AITeamVN/Vietnamese_Embedding"
DB_NAME = "movie_database"
COLLECTION_NAME = "movies"
MONGO_URI = "mongodb://localhost:27017/"

# ========== KHỞI TẠO ==========
os.makedirs(VECTOR_DIR, exist_ok=True)
client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]
model = SentenceTransformer(EMBEDDING_MODEL_NAME)
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

# ========== TẠO VECTOR DB ==========
def create_db():
    prompts = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2048, chunk_overlap=50)

    for doc in collection.find():
        try:
            name = doc.get("name", "").strip()
            if not name:
                continue

            genres = ', '.join(doc.get("genre", []))
            duration = str(doc.get("duration", "")).strip()
            director = doc.get("director", "").strip()
            actors = ', '.join(doc.get("actor", []))
            year = str(doc.get("year_of_release", "")).strip()
            description = doc.get("describe", "").strip()

            # Prompt mô tả thông tin chung
            info_prompt = (
                f"{name} là một bộ phim thể loại {genres}"
                f"{', kéo dài ' + duration + ' phút' if duration else ''}"
                f"{', được đạo diễn bởi ' + director if director else ''}"
                f"{', với sự tham gia của các diễn viên ' + actors if actors else ''}"
                f"{', ra mắt vào năm ' + year if year else ''}."
                f"{', Nội dung tóm tắt ngắn gọn của phim là ' + description if description else ''}"
            ).strip()
            prompts.append(info_prompt)

        except Exception as e:
            print(f"Lỗi khi xử lý phim '{doc.get('name', 'Unknown')}': {e}")

    if not prompts:
        print("❌ Không có prompt nào để tạo index.")
        return

    # Tạo chunks từ các prompt
    docs = [Document(page_content=p) for p in prompts]
    chunks = text_splitter.split_documents(docs)

    # Tạo FAISS index LangChain với chunks
    vectorstore = FAISS.from_documents(chunks, embedding=embedding_wrapper)
    vectorstore.save_local(VECTOR_DIR)

    print(f"✅ Đã lưu FAISS index tại thư mục: {VECTOR_DIR}")
    print(f"🎬 Tổng số prompt đã tạo: {len(prompts)}")

# ========== CHẠY CHÍNH ==========
create_db()
