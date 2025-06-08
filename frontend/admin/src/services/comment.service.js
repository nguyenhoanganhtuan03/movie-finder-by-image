import createApiClient from "./api.service.js";

class CommentService {
  constructor(baseUrl = "/api/comment") {
    this.api = createApiClient(baseUrl);
  }

  // Gửi comment mới
  async create(data) {
    return await this.api.post("/create_comment", data);
  }

  // Lấy danh sách comment theo movie_id
  async getByMovieId(movieId) {
    return await this.api.get(`/movie/${movieId}`);
  }
  
  // Xóa comment theo comment_id
  async delete(commentId) {
    return await this.api.delete(`/${commentId}`);
  }
}

export default new CommentService();
