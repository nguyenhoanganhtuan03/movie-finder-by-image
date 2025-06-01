import os
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from pyvi.ViTokenizer import tokenize

from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# ========== CẤU HÌNH ==========
VECTOR_DIR = "vector_db/movie_vector_db"
EMBEDDING_MODEL_NAME = "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
DB_NAME = "movie_database"
COLLECTION_NAME = "movies"
MONGO_URI = "mongodb://localhost:27017/"

# ========== KHỞI TẠO ==========
os.makedirs(VECTOR_DIR, exist_ok=True)
client = MongoClient(MONGO_URI)
collection = client[DB_NAME][COLLECTION_NAME]
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# ========== WRAPPER EMBEDDING CHO LANGCHAIN ==========
class SentenceTransformerEmbeddingWrapper(Embeddings):
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        # texts là list[str]
        tokenized = [tokenize(t.strip().lower()) for t in texts]
        embeddings = self.model.encode(tokenized, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text):
        tokenized = tokenize(text.strip().lower())
        embedding = self.model.encode([tokenized], convert_to_numpy=True)[0]
        return embedding.tolist()

embedding_wrapper = SentenceTransformerEmbeddingWrapper(model)

# ========== TẠO VECTOR DB ==========
def create_db():
    prompts = []

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

            prompt = (
                f"{name} là một bộ phim thể loại {genres}"
                f"{', kéo dài ' + duration + ' phút' if duration else ''}"
                f"{', được đạo diễn bởi ' + director if director else ''}"
                f"{', với sự tham gia của ' + actors if actors else ''}"
                f"{', ra mắt vào năm ' + year if year else ''}. "
                f"{'Nội dung phim: ' + description if description else ''}"
            ).strip()

            prompts.append(prompt)

        except Exception as e:
            print(f"Lỗi khi xử lý phim '{doc.get('name', 'Unknown')}': {e}")

    if not prompts:
        print("❌ Không có prompt nào để tạo index.")
        return

    # Tạo chunks từ prompts
    docs = [Document(page_content=p) for p in prompts]

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    chunks = text_splitter.split_documents(docs)

    # Tạo FAISS index LangChain với chunks
    vectorstore = FAISS.from_documents(chunks, embedding=embedding_wrapper)
    vectorstore.save_local(VECTOR_DIR)

    print(f"✅ Đã lưu FAISS index tại thư mục: {VECTOR_DIR}")
    print(f"🎬 Tổng số phim đã xử lý: {len(prompts)}")


# ========== CHẠY CHÍNH ==========
if __name__ == "__main__":
    create_db()
