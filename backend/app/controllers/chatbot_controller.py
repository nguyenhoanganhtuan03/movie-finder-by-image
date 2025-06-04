from app.database import db
from pymongo import ReturnDocument

from app.models.models_nlp.run_chatbot_api import MovieQASystem

# Hàm xử lý ChatBot
async def chatbot(content: str):
    qa_system = MovieQASystem()
    question = content.strip()

    answer = qa_system.answer_question(question)
    return answer