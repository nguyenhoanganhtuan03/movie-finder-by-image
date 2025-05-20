<template>
    <div class="container">
      <div class="row">
        <!-- Hiển thị các MovieCard, chỉ hiển thị tối đa 4 bộ phim ban đầu -->
        <MovieCard
          v-for="movie in displayedMovies"
          :key="movie._id"
          :movie="movie"
        />
      </div>
  
      <!-- Nút "Xem thêm phim" chỉ hiển thị khi có nhiều hơn 4 phim -->
      <div v-if="movies.length > 4" class="text-center mt-4">
        <button class="btn btn-primary" @click="showMoreMovies">
          Xem thêm phim
        </button>
      </div>
    </div>
  </template>
  
  <script>
  import MovieCard from "@/components/movies/movieCard.vue";
  import MovieService from "@/services/movie.service";
  
  export default {
    name: "MovieList",
    components: {
      MovieCard,
    },
    props: {
      search: {
        type: String,
        default: "",
      },
    },
    data() {
      return {
        movies: [],
        // Biến để lưu trữ số lượng phim đã hiển thị
        displayedMoviesCount: 4,
      };
    },
    computed: {
      filteredMovies() {
        if (!this.search) return this.movies;
        const query = this.search.toLowerCase();
        return this.movies.filter((movie) =>
          movie.name.toLowerCase().includes(query)
        );
      },
      displayedMovies() {
        // Lấy ra các phim cần hiển thị, tối đa 4 phim đầu tiên
        return this.filteredMovies.slice(0, this.displayedMoviesCount);
      },
    },
    async created() {
      // Lấy tất cả phim từ API
      this.movies = await MovieService.getAll();
    },
    methods: {
      // Hàm để hiển thị thêm các phim khi nhấn nút "Xem thêm phim"
      showMoreMovies() {
        this.displayedMoviesCount += 4; // Mỗi lần nhấn sẽ hiển thị thêm 4 phim
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
  