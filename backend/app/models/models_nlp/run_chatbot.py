import os
from sentence_transformers import SentenceTransformer
from pyvi.ViTokenizer import tokenize

from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from langchain_community.llms import CTransformers
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# ==== CẤU HÌNH ====
VECTOR_DIR = "vector_db/movie_vector_db"
MODELS_LLM_DIR = "models_llm"
EMBEDDING_MODEL = "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
LLM_MODEL_PATH = os.path.join(MODELS_LLM_DIR, "vinallama-7b-chat_q5_0.gguf")

# ==== LOAD MODEL EMBEDDING & LLM ====
model = SentenceTransformer(EMBEDDING_MODEL)

llm = CTransformers(
    model=LLM_MODEL_PATH,
    model_type="llama",
    config={"max_new_tokens": 1024, "temperature": 0.01}
)

# ========== WRAPPER EMBEDDING CHO LANGCHAIN ==========
class SentenceTransformerEmbeddingWrapper(Embeddings):
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        tokenized = [tokenize(t.strip().lower()) for t in texts]
        embeddings = self.model.encode(tokenized, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text):
        tokenized = tokenize(text.strip().lower())
        embedding = self.model.encode([tokenized], convert_to_numpy=True)[0]
        return embedding.tolist()

embedding_wrapper = SentenceTransformerEmbeddingWrapper(model)

# ==== PROMPT TEMPLATE VỚI 2 BIẾN: query và context ====
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
        Bạn là trợ lý AI. Hãy trả lời người dùng một cách chính xác và có thể tin cậy. 
        Chỉ trả lời 1 lần duy nhất. Không dài dòng.
        Nếu bạn không biết câu trả lời, hãy nói rằng bạn không biết.

        Thông tin liên quan:
        {context}

        Câu hỏi: {question}
        """
)

# ==== TẠO CHAIN TRẢ LỜI DỰA TRÊN VECTORSTORE ====
def create_qa_chain(llm, db):
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_template}
    )
    return qa_chain

# ==== ĐỌC VECTORSTORE FAISS ====
def read_vectors_db():
    if not os.path.exists(VECTOR_DIR):
        raise FileNotFoundError(f"Thư mục vector DB không tồn tại: {VECTOR_DIR}")
    db = FAISS.load_local(VECTOR_DIR, embedding_wrapper, allow_dangerous_deserialization=True)
    return db

# ==== MAIN ====
if __name__ == "__main__":
    try:
        db = read_vectors_db()
    except Exception as e:
        print(f"❌ Lỗi khi load vector DB: {e}")
        exit(1)

    llm_chain = create_qa_chain(llm, db)

    while True:
        question = input("Nhập câu hỏi (gõ 'quit' để thoát): ").strip()
        if question.lower() == "quit":
            print("👋 Kết thúc chương trình.")
            break

        # Dùng invoke với dict có key là biến query
        response = llm_chain.invoke({"query": question})
        print("\n🤖 Trả lời:\n", response['result'])
        print("-" * 50)
