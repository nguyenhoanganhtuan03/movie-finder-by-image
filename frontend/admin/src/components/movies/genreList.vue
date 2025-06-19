<template>
    <div class="container">
      <div class="row">
        <!-- Hiển thị các MovieCard, chỉ hiển thị tối đa N phim ban đầu -->
        <MovieCard
          v-for="movie in displayedMovies"
          :key="movie._id"
          :movie="movie"
        />
      </div>
  
      <!-- Nút "Xem thêm phim" chỉ hiển thị khi có nhiều hơn 4 phim -->
      <div v-if="filteredMovies.length > 4 && displayedMovies.length < filteredMovies.length" class="text-center mt-4">
        <button class="btn btn-primary" @click="showMoreMovies">
          Xem thêm phim
        </button>
      </div>
    </div>
  </template>
  
  <script>
  import MovieCard from "@/components/movies/movieCard.vue";
  
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
      movies: {
        type: Array,
        default: () => [],
      },
    },
    data() {
      return {
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
        return this.filteredMovies.slice(0, this.displayedMoviesCount);
      },
    },
    methods: {
      showMoreMovies() {
        this.displayedMoviesCount += 4;
      },
    },
    watch: {
      movies() {
        // Reset lại số phim hiển thị khi thay đổi danh sách phim
        this.displayedMoviesCount = 4;
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
  