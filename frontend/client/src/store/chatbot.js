import { defineStore } from 'pinia';

export const useChatbotStore = defineStore('chatbot', {
  state: () => ({
    currentChatId: null,
  }),
  actions: {
    setChatId(id) {
      this.currentChatId = id;
    },
    clearChatId() {
      this.currentChatId = null;
    },
  },
});