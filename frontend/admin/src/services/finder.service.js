import createApiClient from "./api.service.js";
import axios from "axios";

class FinderService {
    constructor(baseUrl = "/api/finder") {
        this.api = createApiClient(baseUrl);
    }

    // Gửi truy vấn văn bản và nhận danh sách phim
    async searchByContent(content) {
        if (!content) {
            throw new Error("Nội dung tìm kiếm không được để trống.");
        }

        try {
            const response = await this.api.post("/search_by_content", {
                content: content
            });

            // Trả về danh sách tên phim
            return response.data;
        } catch (error) {
            console.error("Lỗi khi tìm phim:", error);
            throw error;
        }
    }
}

export default new FinderService();
