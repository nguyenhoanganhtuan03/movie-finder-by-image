<template>
  <div class="col-md-3 mb-4">
    <div class="card h-100 shadow-sm position-relative" v-if="movie">
      <!-- Nút xóa -->
      <button
        class="btn btn-sm btn-danger position-absolute top-0 end-0 m-2"
        @click="deleteHistory"
        title="Xóa lịch sử"
      >
        &times;
      </button>

      <img
        :src="movie.poster || defaultPoster"
        class="card-img-top"
        :alt="movie.name"
        style="height: 250px; object-fit: cover"
      />
      <div class="card-body d-flex flex-column">
        <h5 class="card-title">{{ movie.name }}</h5>

        <p class="card-text text-muted" v-if="dateWatched">
          👁️ Đã xem: {{ formatDate(dateWatched) }}
        </p>

        <p class="card-text">
          ⏱ Thời lượng: {{ movie.duration }} phút
        </p>

        <p class="card-text">
          📚 Thể loại:
          <span v-if="movie.genre && movie.genre.length">
            {{ movie.genre.join(", ") }}
          </span>
          <span v-else>
            Không rõ
          </span>
        </p>

        <button class="btn btn-outline-primary mt-auto w-100" @click="goToDetailPage">
          Xem phim
        </button>
      </div>
    </div>

    <div v-else class="text-center p-4">
      Đang tải thông tin phim...
    </div>
  </div>
</template>

<script>
import MovieService from "@/services/movie.service";
import { useAuthStore } from "@/store/auth";
import HistoryService from "@/services/history.service";

export default {
  name: "HistoryCard",
  props: {
    movieId: {
      type: String,
      required: true,
    },
    dateWatched: {
      type: String,
      default: null,
    },
    historyId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      movie: null,
    };
  },
  computed: {
    defaultPoster() {
      return "https://via.placeholder.com/250x350?text=No+Image";
    },
  },
  async mounted() {
    try {
      this.movie = await MovieService.getById(this.movieId);
    } catch (error) {
      console.error("Lỗi lấy thông tin phim:", error);
    }
  },
  methods: {
    async goToDetailPage() {
      const authStore = useAuthStore();

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

      this.$router.push(`/movie/${this.movie._id}`);
    },
    formatDate(dateStr) {
      const date = new Date(dateStr);
      return date.toLocaleDateString("vi-VN");
    },
    async deleteHistory() {
      try {
        await HistoryService.deleteHistoryById(this.historyId);
        this.$emit("history-deleted", this.historyId); // Emit để component cha xóa khỏi danh sách
        console.log("🗑️ Đã xóa lịch sử:", this.historyId);
      } catch (error) {
        console.error("❌ Lỗi khi xóa lịch sử:", error.response?.data || error.message);
      }
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
