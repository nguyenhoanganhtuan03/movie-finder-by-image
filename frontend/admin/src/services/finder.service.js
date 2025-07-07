import createApiClient from "./api.service.js";
import axios from "axios";

class FinderService {
    constructor(baseUrl = "/api/finder") {
        this.api = createApiClient(baseUrl);
    }

    // Gửi truy vấn văn bản và nhận danh sách phim
    async searchByContent(content, similarityThreshold = null, n_movies = null) {
        if (!content) {
            throw new Error("Nội dung tìm kiếm không được để trống.");
        }

        try {
            const formData = new FormData();
            formData.append("content", content);

            if (similarityThreshold !== null && similarityThreshold !== undefined) {
                formData.append("SIMILARITY_THRESHOLD", similarityThreshold);
            }

            if (n_movies !== null && n_movies !== undefined) {
                formData.append("n_movies", n_movies);
            }

            const response = await this.api.post("/search_by_content", formData, {
                headers: {
                    "Content-Type": "multipart/form-data"
                }
            });

            return response.data;
        } catch (error) {
            console.error("Lỗi khi tìm phim:", error);
            throw error;
        }
    }

    // Gửi truy vấn audio và nhận danh sách phim
    async searchByAudio(audio, similarityThreshold = null, n_movies = null) {
        try {
            const formData = new FormData();
            formData.append("audio_file", audio);
    
            if (similarityThreshold !== null && similarityThreshold !== undefined) {
                formData.append("SIMILARITY_THRESHOLD", similarityThreshold);
            }
    
            if (n_movies !== null && n_movies !== undefined) {
                formData.append("n_movies", n_movies);
            }
    
            const response = await this.api.post("/search_by_audio", formData, {
                headers: {
                    "Content-Type": "multipart/form-data"
                }
            });
            console.log(response.data)
    
            return response.data;
        } catch (error) {
            console.error("Lỗi khi tìm phim:", error);
            throw error;
        }
    }
}

export default new FinderService();
