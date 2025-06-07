import createApiClient from "./api.service.js";

class ChatbotService {
  constructor(baseUrl = "/api/chatbot") {
    this.api = createApiClient(baseUrl);
  }

  async sendMessage(userId, content) {
    const payload = { 
      user_id: userId, 
      content 
    };
  
    const { data } = await this.api.post("/", payload);
    console.log(data)
    return {
      answer: data.answer,
      hischat_id: data.hischat_id
    };
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
    console.log(data)
    return data;
  }
}

export default new ChatbotService();