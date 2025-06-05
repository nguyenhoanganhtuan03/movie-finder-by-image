import createApiClient from "./api.service.js";

class ChatbotService {
  constructor(baseUrl = "/api/chatbot") {
    this.api = createApiClient(baseUrl);
  }

  async sendMessage(userId, content, chatId = null) {
    const payload = { 
      user_id: userId, 
      content 
    };
    
    // Thêm chat_id nếu có (để tiếp tục cuộc trò chuyện hiện tại)
    if (chatId) {
      payload.hischat_id = chatId;
    }
    
    const { data } = await this.api.post("/", payload);
    return data;
  }

  async getHistory(userId) {
    const { data } = await this.api.get(`/user/${userId}`);
    return data;
  }

  async updateHistory(hischatId, userMessage) {
    const { data } = await this.api.put("/", {
      hischat_id: hischatId,
      user_message: userMessage
    });
    return data;
  }

  async deleteHistoryById(id) {
    const { data } = await this.api.delete(`/${id}`);
    return data;
  }

  async deleteAllByUser(userId) {
    const { data } = await this.api.delete(`/user/${userId}`);
    return data;
  }

  // Thêm method để lấy chi tiết một cuộc trò chuyện
  async getChatById(chatId) {
    const { data } = await this.api.get(`/${chatId}`);
    return data;
  }
}

export default new ChatbotService();