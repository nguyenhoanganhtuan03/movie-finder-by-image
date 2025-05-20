<template>
  <div>
    <!-- Header -->
    <AppHeader />

    <!-- Main content -->
    <div class="container mt-4">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h3>📖 Lịch sử xem phim</h3>
        <button
          v-if="userId && histories.length > 0"
          class="btn btn-danger btn-sm"
          @click="handleDeleteAll"
          :disabled="deletingAll"
          title="Xóa tất cả lịch sử xem phim"
        >
          {{ deletingAll ? "Đang xóa..." : "Xóa tất cả lịch sử" }}
        </button>
      </div>

      <!-- Nếu chưa đăng nhập -->
      <div v-if="!userId" class="alert alert-warning">
        Vui lòng đăng nhập để xem lịch sử.
      </div>

      <!-- Nếu đang tải dữ liệu -->
      <div v-else-if="loading">
        Đang tải dữ liệu...
      </div>

      <!-- Nếu có lỗi -->
      <div v-else-if="error" class="alert alert-danger">
        Lỗi khi tải lịch sử: {{ error }}
      </div>

      <!-- Nếu có lịch sử thì hiển thị -->
      <div v-else>
        <div v-if="histories.length === 0">
          Không có lịch sử.
        </div>

        <div v-else>
          <div class="row">
            <HistoryCard
              v-for="item in displayedHistories"
              :key="item._id"
              :movie-id="item.movie_id"
              :history-id="item._id"
              :date-watched="item.dateWatched"
              @history-deleted="removeHistory"
            />
          </div>

          <div v-if="histories.length > 4" class="text-center mt-4">
            <button class="btn btn-primary" @click="showMore = !showMore">
              {{ showMore ? "Thu gọn lịch sử" : "Xem thêm lịch sử" }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <AppFooter />
  </div>
</template>

<script>
import { useAuthStore } from "@/store/auth";
import AppHeader from "@/components/common/AppHeader.vue";
import AppFooter from "@/components/common/AppFooter.vue";
import HistoryCard from "@/components/histories/historyCard.vue";
import HistoryService from "@/services/history.service.js";

export default {
  name: "HistoryPage",
  components: {
    AppHeader,
    AppFooter,
    HistoryCard,
  },
  data() {
    return {
      histories: [],
      loading: false,
      error: null,
      userId: null,
      showMore: false,
      deletingAll: false,
    };
  },
  computed: {
    displayedHistories() {
      const reversed = [...this.histories].reverse();
      return this.showMore ? reversed : reversed.slice(0, 4);
    },
  },
  async mounted() {
    const authStore = useAuthStore();
    this.userId = authStore.user?.id || null;

    if (!this.userId) {
      console.warn("Chưa đăng nhập, không thể tải lịch sử.");
      return;
    }

    this.loading = true;
    try {
      const response = await HistoryService.getHistoriesByUserId(this.userId);
      this.histories = response;
    } catch (err) {
      this.error = err.message || "Lỗi không xác định";
      console.error("Lỗi khi tải lịch sử xem phim:", err);
    } finally {
      this.loading = false;
    }
  },
  methods: {
    removeHistory(historyId) {
      this.histories = this.histories.filter((item) => item._id !== historyId);
    },
    async handleDeleteAll() {
      if (!this.userId) return;
      if (!confirm("Bạn có chắc chắn muốn xóa tất cả lịch sử xem phim?")) return;

      this.deletingAll = true;
      try {
        await HistoryService.deleteHistoriesByUserId(this.userId);
        this.histories = [];
        this.showMore = false;
        console.log("🗑 Đã xóa tất cả lịch sử xem phim.");
      } catch (error) {
        console.error("❌ Lỗi khi xóa tất cả lịch sử:", error);
        alert("Xảy ra lỗi khi xóa tất cả lịch sử. Vui lòng thử lại.");
      } finally {
        this.deletingAll = false;
      }
    },
  },
};
</script>
