from fastapi import HTTPException
from pymongo import ReturnDocument
from typing import List
from datetime import datetime

from app.database import db
from app.models.models_nlp.run_chatbot_api import MovieQASystem
from app.entities.chatbot_model import HistoryChatbotModel


# Tạo ID tăng tự động 
async def get_next_id(): 
    result = await db["counters"].find_one_and_update(
        {"_id": "hischat_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.BEFORE
    )
    if result is None:
        return "hischat_1"
    else:
        return f"hischat_{result['seq'] + 1}"


# Hàm tạo lịch sử chat
async def create_his_chat(data: HistoryChatbotModel):
    if not data._id:
        hischat_id = await get_next_id()
    
    data_dict = data.dict()
    data_dict["_id"] = hischat_id 
    
    result = await db['history_chatbot'].insert_one(data_dict)
    
    return hischat_id


# Hàm xử lý ChatBot
async def chatbot(user_id: str, content: str):
    qa_system = MovieQASystem()
    question = content.strip()
    answer = qa_system.answer_question(question)
    history_data = HistoryChatbotModel(
        user_id=user_id,
        content=[  
            {
                "user": question,
                "bot": answer
            }
        ]
    )

    saved_record = await create_his_chat(history_data)
    return {
        "answer": answer,
        "hischat_id": str(saved_record) 
    }


# Lấy tất cả lịch sử chat theo user_id
async def get_his_chat_by_user(user_id: str) -> List[HistoryChatbotModel]:
    cursor = db["history_chatbot"].find({"user_id": user_id}).sort("date_chat", -1) 
    results = []
    async for document in cursor:
        document["_id"] = str(document["_id"])
        results.append(document)
    return results


# Lấy thông tin lịch sử chat theo hischat_id
async def get_his_chat_by_id(hischat_id: str):
    cursor = db["history_chatbot"].find({"_id": hischat_id})
    results = []
    async for document in cursor:
        results.append(HistoryChatbotModel(**document))
    return results


# Hàm cập nhật hischat
async def update_his_chat(hischat_id: str, user_message: str):
    qa_system = MovieQASystem()
    bot_answer = qa_system.answer_question(user_message)
    update_doc = {
        "$push": {
            "content": {
                "user": user_message,
                "bot": bot_answer
            }
        },
        "$set": {
            "date_chat": datetime.utcnow().isoformat() 
        }
    }
    result = await db['history_chatbot'].find_one_and_update(
        {"_id": hischat_id},
        update_doc,
        return_document=ReturnDocument.AFTER
    )
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử chat")
    return result


# Hàm xóa lịch sử chatbot
async def delete_his_chat(chat_id: str):
    result = await db["history_chatbot"].delete_one({"_id": chat_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy lịch sử với id: {chat_id}")
    
    return {"message": f"Đã xóa lịch sử với id: {chat_id}"}


# Hàm xóa toàn bộ lịch sử chat theo user_id
async def delete_all_his_chat_by_user(user_id: str):
    result = await db["history_chatbot"].delete_many({"user_id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy lịch sử chat nào cho user_id: {user_id}")
    
    return {
        "message": f"Đã xóa {result.deleted_count} lịch sử chat của user_id: {user_id}"
    }