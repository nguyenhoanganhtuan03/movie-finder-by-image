
import { defineStore } from "pinia";
import { useChatbotStore } from '@/store/chatbot';

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    isAuthenticated: false,
  }),
  getters: {
    // Getter để xác định người dùng có đăng nhập hay không
    isLoggedIn: (state) => !!state.user, // Nếu có user thì là true
  },
  actions: {
    login(userData) {
      this.user = userData; // Lưu thông tin user vào state
      this.isAuthenticated = true;
      console.log("🔹 User logged in:", this.user);
    },
    logout() {
      this.user = null;
      this.isAuthenticated = false;
      const chatbotStore = useChatbotStore();
      chatbotStore.clearChatId();
      console.log("🔹 User logged out");
    },
  },
});
