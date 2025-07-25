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

  async searchByFile(file, similarityThreshold, n_movies) {
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("similarity_threshold", similarityThreshold);
      formData.append("n_movies", n_movies);
  
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

  async getByGenre(genre) {
    try {
      const response = await this.api.post(`/genre`, {
        genre: genre
      });
      console.log(response.data)
      return response.data || [];
    } catch (error) {
      console.error("Lỗi khi lấy phim theo thể loại:", error);
      return [];
    }
  }

  async getGenres() {
    try {
        const response = await this.api.get("/genres");
        return response.data || [];
    } catch (error) {
        console.error("Lỗi khi lấy danh sách thể loại:", error);
        return [];
    }
  }

  async getByYear(year) {
    try {
      const response = await this.api.get(`/yor/${year}`);
      return response.data || [];
    } catch (error) {
      console.error("Lỗi khi lấy phim theo năm:", error);
      return [];
    }
  }

}

export default new MovieService();