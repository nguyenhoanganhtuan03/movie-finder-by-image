import createApiClient from "./api.service.js";

class Sp2TextService {
    constructor(baseUrl = "/api/sp2text") {
        this.api = createApiClient(baseUrl);
    }

    async getTextFromSpeech() {
        try {
            const res = await this.api.get("/");
            console.log(res)
            return res.data;
        } catch (err) {
            console.error("Lỗi khi gọi API speech-to-text:", err);
            return { error: "Không thể gọi API" };
        }
    }
}

export default new Sp2TextService();
