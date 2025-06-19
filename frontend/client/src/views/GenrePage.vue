<template>
    <div>
      <!-- Header -->
      <AppHeader />
  
      <!-- Nội dung trang -->
      <div class="container mt-4">
        <!-- Tiêu đề -->
        <div class="text-center mb-4">
          <h1 class="display-5">Trang thể loại</h1>
          <p class="lead">Thư viện phim trực tuyến</p>
        </div>
  
        <!-- Chọn thể loại 1 -->
        <div class="row mb-4">
            <div class="col-md-6">
                <label for="genre1Select" class="form-label">Thể loại 1:</label>
                <select
                id="genre1Select"
                v-model="genre1"
                class="form-select"
                >
                <option value="">-- Chọn thể loại --</option>
                <option v-for="genre in genres" :key="genre" :value="genre">
                    {{ genre }}
                </option>
                </select>
            </div>

            <div class="col-md-6">
                <label for="genre2Select" class="form-label">Thể loại 2: (nếu có)</label>
                <select
                id="genre2Select"
                v-model="genre2"
                class="form-select"
                >
                <option value="">-- Chọn thể loại --</option>
                <option v-for="genre in genres" :key="genre" :value="genre">
                    {{ genre }}
                </option>
                </select>
            </div>
        </div>

        <!-- Danh sách phim -->
        <GenreList :movies="moviesByGenre" />
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
  
      <!-- Footer -->
      <AppFooter />
    </div>
  </template>
  
  <script>
  import AppHeader from "@/components/common/AppHeader.vue";
  import AppFooter from "@/components/common/AppFooter.vue";
  import GenreList from "@/components/movies/genreList.vue";
  import MiniChatWidget from "@/components/chatbot/ChatbotWidget.vue";
  import MovieService from "@/services/movie.service";
  
  export default {
    name: "HomePage",
    components: {
      AppHeader,
      AppFooter,
      GenreList,
      MiniChatWidget,
    },
  data() {
    return {
      isChatOpen: false,
      genres: [],
      genre1: "",       // Không gán mặc định
      genre2: "",
      allMovies: [],    // Tất cả phim
      moviesByGenre: [],// Kết quả lọc
    };
  },
  methods: {
    async fetchGenresAndMovies() {
      try {
        this.genres = await MovieService.getGenres();
        this.allMovies = await MovieService.getAll();
        this.moviesByGenre = [...this.allMovies]; // Hiển thị tất cả ban đầu
      } catch (error) {
        console.error("Lỗi khi lấy dữ liệu:", error);
      }
    },
    filterMovies() {
      let filtered = [...this.allMovies];

      if (this.genre1) {
        filtered = filtered.filter((movie) =>
          movie.genre && movie.genre.includes(this.genre1)
        );
      }

      if (this.genre2) {
        filtered = filtered.filter((movie) =>
          movie.genre && movie.genre.includes(this.genre2)
        );
      }

      this.moviesByGenre = filtered;
    },
  },
  watch: {
    genre1: "filterMovies",
    genre2: "filterMovies",
  },
  mounted() {
    this.fetchGenresAndMovies();
  },
};
  </script>
  