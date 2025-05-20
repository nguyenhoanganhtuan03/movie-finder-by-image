import createApiClient from "./api.service.js";

class HistoryService {
    constructor(baseUrl = "/api/history") {
        this.api = createApiClient(baseUrl);
    }

    // 🆕 Thêm lịch sử xem
    async addHistory(data) {
        try {
            const response = await this.api.post("/add_history", data);
            return response.data;
        } catch (error) {
            console.error("❌ Lỗi khi thêm lịch sử:", error.response?.data || error.message);
            throw error;
        }
    }

    // Lấy toàn bộ lịch sử xem của user
    async getHistoriesByUserId(userId) {
        try {
            const response = await this.api.get(`/histories/${userId}`);
            return response.data;
        } catch (error) {
            console.error("❌ Lỗi khi lấy lịch sử:", error.response?.data || error.message);
            throw error;
        }
    }

    // Xóa toàn bộ lịch sử của user
    async deleteHistoriesByUserId(userId) {
        try {
            const response = await this.api.delete(`/histories/${userId}`);
            return response.data;
        } catch (error) {
            console.error("❌ Lỗi khi xóa toàn bộ lịch sử:", error.response?.data || error.message);
            throw error;
        }
    }

    // 🆕 Xóa một mục lịch sử cụ thể
    async deleteHistoryById(historyId) {
        try {
            const response = await this.api.delete(`/${historyId}`);
            return response.data;
        } catch (error) {
            console.error("❌ Lỗi khi xóa lịch sử:", error.response?.data || error.message);
            throw error;
        }
    }
}

export default new HistoryService();
