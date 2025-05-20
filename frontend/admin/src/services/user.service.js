import createApiClient from "./api.service.js";

class UserService {
    constructor(baseUrl = "/api/user") {
        this.api = createApiClient(baseUrl);
    }

    async register(userData) {
        try {
            const data = (await this.api.post("/register", userData)).data;
            return {
                status: "success",
                message: data.message || "User registered successfully",
                data: data.data,
            };
        } catch (err) {
            return {
                status: "error",
                message: err.response?.data?.message || "Registration failed",
            };
        }
    }

    async login(credentials) {
        try {
            const response = await this.api.post("/login", credentials);
            console.log("✅ API Response:", response.data);

            return {
                status: "success",
                message: response.data.message || "Login successful",
                user: response.data.user,  
            };
        } catch (err) {
            console.error("🔴 API Login Error:", err.response?.data || err.message);

            return {
                status: "error",
                message: err.response?.data?.message || "Login failed",
            };
        }
    }

    async getUserById(userId) {
        try {
            const response = await this.api.get(`/${userId}`);
            return {
                status: "success",
                user: response.data,
            };
        } catch (err) {
            console.error("🔴 API Get User Error:", err.response?.data || err.message);
            return {
                status: "error",
                message: err.response?.data?.message || "Failed to get user info",
            };
        }
    }

    // ✅ Thêm: Cập nhật mật khẩu
    async updatePassword(userId, passwordData) {
        try {
            const response = await this.api.put(`/users/update-password/${userId}`, passwordData);
            return {
                status: "success",
                message: response.data.message || "Password updated successfully",
            };
        } catch (err) {
            return {
                status: "error",
                message: err.response?.data?.message || "Failed to update password",
            };
        }
    }

    // ✅ Thêm: Xóa người dùng
    async deleteUser(userId) {
        try {
            const response = await this.api.delete(`/users/${userId}`);
            return {
                status: "success",
                message: response.data.message || "User deleted successfully",
            };
        } catch (err) {
            return {
                status: "error",
                message: err.response?.data?.message || "Failed to delete user",
            };
        }
    }

}

export default new UserService();