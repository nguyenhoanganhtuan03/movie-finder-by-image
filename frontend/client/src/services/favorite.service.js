import createApiClient from "./api.service.js";

class FavoriteService {
  constructor(baseUrl = "/api/favorite") {
    this.api = createApiClient(baseUrl);
  }

  // Gọi API POST /add_favorite để thêm phim yêu thích
  async addToFavorites(userId, movieId) {
    try {
      const response = await this.api.post("/add_favorite", {
        user_id: userId,
        movie_id: movieId,
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // Gọi API GET /favorites/{user_id} để lấy danh sách phim yêu thích
  async getFavoritesByUserId(userId) {
    try {
      const response = await this.api.get(`/favorites/${userId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

    // 🆕 Xóa một mục favorite cụ thể
    async deleteFavoriteById(favoriteId) {
        try {
            const response = await this.api.delete(`/favorites/${favoriteId}`);
            return response.data;
        } catch (error) {
            console.error("❌ Lỗi khi xóa lịch sử:", error.response?.data || error.message);
            throw error;
        }
    }
}

export default new FavoriteService();
