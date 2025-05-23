import createApiClient from "./api.service.js";
import axios from "axios";

class MovieService {
    constructor(baseUrl = "/api/movie") {
        this.api = createApiClient(baseUrl);
    }

  async getAll() {
    try {
      const response = await this.api.get("/movies");
      return response.data.movies || response.data; // hỗ trợ cả 2 kiểu response
    } catch (error) {
      console.error("Lỗi khi lấy danh sách phim:", error);
      return [];
    }
  }

  async getById(id) {
    try {
      const response = await this.api.get(`/movies/${id}`);
      console.log(response.data)
      return response.data;
    } catch (error) {
      console.error("Lỗi khi lấy phim theo ID:", error);
      return null;
    }
  }

  async searchByName(name) {
    try {
      const response = await this.api.get(`/search`, {
        params: { name },
      });
      return response.data || [];
    } catch (error) {
      console.error("Lỗi khi tìm kiếm phim:", error);
      return [];
    }
  }

  async searchByFile(file) {
    try {
      const formData = new FormData();
      formData.append("file", file);
  
      const response = await this.api.post("/search-by-file", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
  
      return response.data;
    } catch (error) {
      console.error("Lỗi khi tìm kiếm phim bằng file:", error);
      return null;
    }
  }
}

export default new MovieService();