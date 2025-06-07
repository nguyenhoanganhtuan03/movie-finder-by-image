import createApiClient from "./api.service.js";

class RatingService {
    constructor(baseUrl = "/api/rating") {
        this.api = createApiClient(baseUrl);
    }

    // Tạo rating đầu tiên cho movie
    async createRating(movieId, firstScore) {
        return (await this.api.post("/", {
            movie_id: movieId,
            first_score: firstScore
        })).data;
    }

    // Lấy rating theo movie_id
    async getRatingByMovieId(movieId) {
        return (await this.api.get(`/${movieId}`)).data;
    }

    // Thêm điểm mới vào rating đã có
    async addRatingScore(movieId, newScore) {
        return (await this.api.put("/", {
            movie_id: movieId,
            new_score: newScore
        })).data;
    }

    // Xoá rating theo rating_id
    async deleteRating(ratingId) {
        return (await this.api.delete(`/${ratingId}`)).data;
    }
}

export default new RatingService();
