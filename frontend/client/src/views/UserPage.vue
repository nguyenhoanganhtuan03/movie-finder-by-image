<template>
  <div class="user-page">
    <AppHeader />

    <main class="main-container">
      <UserDetail />
    </main>

    <!-- Nút bật chatbot -->
    <button
      v-if="!isChatOpen"
      class="btn btn-primary position-fixed bottom-0 end-0 m-4 rounded-circle shadow"
      style="width: 60px; height: 60px; z-index: 10000;"
      @click="isChatOpen = true"
    >
      <i class="bi bi-chat-dots-fill fs-4"></i>
    </button>

    <button
      v-if="!isChatOpen"
      @click="isChatOpen = true"
      class="btn btn-primary rounded-circle shadow-lg"
      style="position: fixed; bottom: 24px; right: 24px; width: 60px; height: 60px; z-index: 9999;"
    >
      <i class="bi bi-robot fs-4"></i>
    </button>

    <!-- Chatbot widget -->
    <MiniChatWidget v-if="isChatOpen" @close="isChatOpen = false" />

    <AppFooter />
  </div>
</template>

<script>
import AppHeader from "@/components/common/AppHeader.vue";
import AppFooter from "@/components/common/AppFooter.vue";
import UserDetail from "@/components/users/userDetail.vue";
import MiniChatWidget from "@/components/chatbot/ChatbotWidget.vue";

export default {
  name: "UserPage",
  components: {
    AppHeader,
    AppFooter,
    UserDetail,
    MiniChatWidget,
  },
  data() {
    return {
      isChatOpen: false,
    };
  },
};
</script>

<style scoped>
.main-container {
  min-height: calc(100vh - 160px); /* trừ header + footer */
  padding: 40px 20px;
  background-color: #f5f5f5;
}
</style>
