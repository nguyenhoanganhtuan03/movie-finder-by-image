import createApiClient from "./api.service";

class StaffService {
    constructor(baseUrl = "/api/staff") {
        this.api = createApiClient(baseUrl);
    }

    async Stafflogin(credentials) {
        try {
            const response = await this.api.post("/login", credentials);
            return {
                status: "success",
                message: response.data.message || "Login successful",
                user: response.data.staff,
            };
        } catch (err) {
            return {
                status: "error",
                message: err.response?.data?.message || "Login failed",
            };
        }
    }
}

export default new StaffService();