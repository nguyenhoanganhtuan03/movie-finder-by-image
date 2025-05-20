<template>
  <div class="col-md-3 mb-4">
    <div class="card h-100 shadow-sm">
      <img
        :src="movie.poster || defaultPoster"
        class="card-img-top"
        :alt="movie.name"
        style="height: 250px; object-fit: cover"
      />
      <div class="card-body d-flex flex-column">
        <h5 class="card-title">{{ movie.name }}</h5>

        <p class="card-text">⏱ Thời lượng: {{ movie.duration }} phút</p>

        <p class="card-text">
          📚 Thể loại:
          <span v-if="movie.genre && movie.genre.length">
            {{ movie.genre.join(", ") }}
          </span>
          <span v-else>Không rõ</span>
        </p>

        <button class="btn btn-outline-primary mt-auto w-100" @click="handleWatchMovie">
          Xem phim
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { useAuthStore } from "@/store/auth";
import HistoryService from "@/services/history.service";

export default {
  name: "MovieCard",
  props: {
    movie: {
      type: Object,
      required: true,
    },
  },
  computed: {
    defaultPoster() {
      return "https://via.placeholder.com/250x350?text=No+Image";
    },
  },
  methods: {
    async handleWatchMovie() {
      const authStore = useAuthStore();

      // Nếu chưa đăng nhập thì không ghi lịch sử
      if (authStore.isLoggedIn) {
        try {
          await HistoryService.addHistory({
            user_id: authStore.user.id,
            movie_id: this.movie._id,
          });
          console.log("✅ Đã ghi lịch sử xem phim.");
        } catch (error) {
          console.error("❌ Lỗi khi ghi lịch sử:", error);
        }
      }

      // Điều hướng tới trang chi tiết phim
      this.$router.push(`/movie/${this.movie._id}`);
    },
  },
};
</script>

<style scoped>
.card-title {
  font-size: 1.2rem;
  font-weight: bold;
}
.card-text {
  font-size: 0.95rem;
  color: #555;
}
</style>
