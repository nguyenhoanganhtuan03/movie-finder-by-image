import createApiClient from "./api.service.js";

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

    // 🔹 Thêm phim mới
    async addMovie(movieData) {
        try {
            const response = await this.api.post("/add_movie", movieData);
            return {
                status: "success",
                message: response.data.message || "Thêm phim thành công",
                data: response.data,
            };
        } catch (error) {
            console.error("Lỗi khi thêm phim:", error);
            return {
                status: "error",
                message: error.response?.data?.detail || "Thêm phim thất bại",
            };
        }
    }

    // 🔹 Cập nhật phim theo ID
    async updateMovie(movieId, updateData) {
        try {
            const response = await this.api.put(`/update_movie/${movieId}`, updateData);
            return {
                status: "success",
                message: response.data.message || "Cập nhật phim thành công",
                data: response.data,
            };
        } catch (error) {
            console.error("Lỗi khi cập nhật phim:", error);
            return {
                status: "error",
                message: error.response?.data?.detail || "Cập nhật phim thất bại",
            };
        }
    }

    // 🔹 Xóa phim theo ID
    async deleteMovie(movieId) {
        try {
            const response = await this.api.delete(`/delete_movie/${movieId}`);
            return {
                status: "success",
                message: response.data.message || "Xóa phim thành công",
            };
        } catch (error) {
            console.error("Lỗi khi xóa phim:", error);
            return {
                status: "error",
                message: error.response?.data?.detail || "Xóa phim thất bại",
            };
        }
    }
}

export default new MovieService();
