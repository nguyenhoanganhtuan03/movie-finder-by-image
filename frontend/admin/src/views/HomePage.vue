<template>
  <div>
    <!-- Header -->
    <AppHeader />

    <!-- Nội dung trang -->
    <div class="container mt-4">
      <!-- Tiêu đề -->
      <div class="text-center mb-4">
        <h1 class="display-5">Trang xem phim</h1>
        <p class="lead">Thư viện phim trực tuyến</p>
      </div>

      <!-- Thanh tìm kiếm -->
      <div class="input-group mb-4">
        <input
          v-model="searchQuery"
          type="text"
          class="form-control"
          placeholder="Tìm tên phim..."
        />
      </div>

      <!-- Danh sách phim -->
      <MovieList :search="searchQuery" />
    </div>

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

    <!-- Footer -->
    <AppFooter />
  </div>
</template>

<script>
import AppHeader from "@/components/common/AppHeader.vue";
import AppFooter from "@/components/common/AppFooter.vue"; 
import MovieList from "@/components/movies/movieList.vue";
import MiniChatWidget from "@/components/chatbot/ChatbotWidget.vue";

export default {
  name: "HomePage",
  components: {
    AppHeader,
    AppFooter,
    MovieList,
    MiniChatWidget
  },
  data() {
    return {
      searchQuery: "",
      isChatOpen: false
    };
  }
};
</script>
