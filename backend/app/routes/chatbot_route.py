from fastapi import APIRouter, FastAPI, Body, Query, Path

from app.controllers.chatbot_controller import (chatbot, get_his_chat_by_user, 
                                                delete_all_his_chat_by_user, delete_his_chat,
                                                update_his_chat, get_his_chat_by_id)
from app.entities.chatbot_model import ChatRequest, UpdateChatRequest

app = FastAPI()
router = APIRouter()

# Route chatbot trả lời
@router.post("/")
async def chatbot_answer(request: ChatRequest):
    response = await chatbot(request.user_id, request.content)
    return response


# Route lấy các hischat theo user_id
@router.get("/user/{user_id}")
async def get_hischat_by_userid(user_id: str = Path(...)):
    return await get_his_chat_by_user(user_id)


# Route lấy lịch sử chat theo _id
@router.get("/{hischat_id}")
async def get_hischat_by_id(hischat_id: str = Path(...)):
    return await get_his_chat_by_id(hischat_id)

# Route cập nhật hischat
@router.put("/")
async def update_hischat(request: UpdateChatRequest):
    # Cập nhật lịch sử chat
    updated_doc = await update_his_chat(request.hischat_id, request.user_message)
    
    return {"updated_history": updated_doc}


# Route xóa một hischat theo _id
@router.delete("/{_id}")
async def delete_by_id(_id: str = Path(...)):
    return await delete_his_chat(_id)


# Route xóa toàn bộ hischat theo user_id
@router.delete("/user/{user_id}")
async def delete_all_by_user_id(user_id: str = Path(...)):
    return await delete_all_his_chat_by_user(user_id)


# Thêm route vào app
app.include_router(router)