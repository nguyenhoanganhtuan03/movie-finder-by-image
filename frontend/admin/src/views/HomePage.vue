<template>
  <div>
    <!-- Header -->
    <AppHeader />

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

      <!-- Danh sách phim theo tìm kiếm -->
      <MovieList :search="searchQuery" />

      <hr>

      <!-- Lọc phim theo khoảng năm -->
      <div class="mb-4 d-flex align-items-center gap-3 flex-wrap">
        <h4 class="mb-0">Phim theo năm</h4>

        <div>
          <select
            v-model="startYear"
            @change="loadMoviesByYearRange"
            class="form-select w-auto"
          >
            <option value="">Chọn năm</option>
            <option v-for="year in availableYears" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </div>

        <div>-</div>

        <div>
          <select
            v-model="endYear"
            @change="loadMoviesByYearRange"
            class="form-select w-auto"
          >
            <option value="">Chọn năm</option>
            <option v-for="year in availableYears" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </div>
      </div>

      <!-- Danh sách phim theo khoảng năm -->
      <div>
        <div v-if="filteredMovies.length">
          <YearList :movies="filteredMovies" />
        </div>

        <div v-else-if="startYear">
          <p class="text-muted fst-italic">Không có phim nào trong khoảng thời gian đã chọn.</p>
        </div>
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

    <MiniChatWidget v-if="isChatOpen" @close="isChatOpen = false" />
    <AppFooter />
  </div>
</template>

<script>
import AppHeader from "@/components/common/AppHeader.vue";
import AppFooter from "@/components/common/AppFooter.vue";
import MovieList from "@/components/movies/movieList.vue";
import YearList from "@/components/movies/yearList.vue";
import MiniChatWidget from "@/components/chatbot/ChatbotWidget.vue";
import MovieService from "@/services/movie.service.js";

export default {
  name: "HomePage",
  components: {
    AppHeader,
    AppFooter,
    MovieList,
    YearList,
    MiniChatWidget
  },
  data() {
    return {
      searchQuery: "",
      isChatOpen: false,
      startYear: 2024,
      endYear: 2025,
      filteredMovies: [],
      availableYears: Array.from({ length: 16 }, (_, i) => 2025 - i), 
    };
  },
  mounted() {
      this.loadMoviesByYearRange(); 
  },
  methods: {
    async loadMoviesByYearRange() {
      if (!this.startYear) {
        this.filteredMovies = [];
        return;
      }

      const from = parseInt(this.startYear);
      const to = this.endYear ? parseInt(this.endYear) : from;

      const moviePromises = [];
      for (let year = from; year <= to; year++) {
        moviePromises.push(MovieService.getByYear(year));
      }

      try {
        const results = await Promise.all(moviePromises);
        this.filteredMovies = results.flat();
      } catch (error) {
        console.error("Lỗi khi tải phim theo khoảng năm:", error);
        this.filteredMovies = [];
      }
    }
  }
};
</script>
