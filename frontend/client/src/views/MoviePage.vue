<template>
  <div>
    <AppHeader />

    <div class="container mt-4">
      <div v-if="loading">Đang tải thông tin phim...</div>
      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-else-if="movie">
        <MovieDetail :movie="movie" />

        <!-- Hiển thị comment -->
        <commentCard class="mt-4" :movieId="movie._id" />
      </div>
      <div v-else>
        Không tìm thấy phim.
      </div>
    </div>

    <!-- Nút bật chatbot -->
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
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import MovieDetail from "@/components/movies/movieDetail.vue";
import AppHeader from "@/components/common/AppHeader.vue";
import AppFooter from "@/components/common/AppFooter.vue";
import commentCard from "@/components/comments/commentCard.vue";
import MovieService from "@/services/movie.service.js";
import MiniChatWidget from "@/components/chatbot/ChatbotWidget.vue";

export default {
  name: "MoviePage",
  components: {
    MovieDetail,
    AppHeader,
    AppFooter,
    commentCard,
    MiniChatWidget,
  },
  setup() {
    const route = useRoute();
    const movieId = route.params.movieId;
    const movie = ref(null);
    const loading = ref(false);
    const error = ref(null);
    const isChatOpen = ref(false);

    onMounted(async () => {
      loading.value = true;
      try {
        movie.value = await MovieService.getById(movieId);
      } catch (err) {
        error.value = err.message || "Lỗi không xác định khi tải phim.";
        console.error("Lỗi tải phim:", err);
      } finally {
        loading.value = false;
      }
    });

    return {
      movie,
      loading,
      error,
      isChatOpen,
    };
  },
};
</script>
