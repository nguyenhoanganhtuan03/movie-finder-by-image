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
  
      <!-- Footer -->
      <AppFooter />
    </div>
  </template>
  
  <script>
  import AppHeader from "@/components/common/AppHeader.vue";
  import AppFooter from "@/components/common/AppFooter.vue"; // Import Footer component
  import MovieList from "@/components/movies/movieList.vue";
  
  export default {
    name: "HomePage",
    components: {
      AppHeader,
      AppFooter, // Register Footer component
      MovieList,
    },
    data() {
      return {
        searchQuery: "",
      };
    },
    methods: {
      onSearch() {
        // Nếu muốn xử lý lọc tại HomePage
      },
    },
  };
  </script>
  
  <style scoped>
  /* Optional: add custom styles for the footer if needed */
  </style>
  