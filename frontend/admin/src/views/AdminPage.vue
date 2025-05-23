<template>
    <div>
      <AppHeader />
  
      <div class="admin-container">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2>Quản lý phim</h2>
          <button class="btn btn-primary" @click="showAddForm = true">+ Thêm phim</button>
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
  
        <!-- Form thêm phim -->
        <div v-if="showAddForm" class="mb-4 border p-3 rounded">
          <h4>Thêm phim mới</h4>
          <form @submit.prevent="handleSubmit">
            <div class="mb-3">
              <label class="form-label">Tên phim</label>
              <input type="text" v-model="form.name" class="form-control" required />
            </div>
  
            <div class="mb-3">
              <label class="form-label">Thời lượng (phút)</label>
              <input type="number" v-model.number="form.duration" class="form-control" required min="1" />
            </div>
  
            <div class="mb-3">
              <label class="form-label">Thể loại (phân cách bằng dấu phẩy)</label>
              <input
                type="text"
                v-model="genreInput"
                @change="updateGenre"
                class="form-control"
                placeholder="Action, Crime, Drama"
              />
            </div>
  
            <div class="mb-3">
              <label class="form-label">Đạo diễn</label>
              <input type="text" v-model="form.director" class="form-control" />
            </div>
  
            <div class="mb-3">
              <label class="form-label">Diễn viên (phân cách bằng dấu phẩy)</label>
              <input
                type="text"
                v-model="actorInput"
                @change="updateActor"
                class="form-control"
                placeholder="Christian Bale, Heath Ledger, Aaron Eckhart"
              />
            </div>
  
            <div class="mb-3">
              <label class="form-label">Năm phát hành</label>
              <input type="number" v-model.number="form.year_of_release" class="form-control" min="1800" max="2100" />
            </div>
  
            <div class="mb-3">
              <label class="form-label">Mô tả</label>
              <textarea v-model="form.describe" class="form-control" rows="3"></textarea>
            </div>
  
            <div class="mb-3">
              <label class="form-label">Chọn file video</label>
              <input type="file" @change="handleVideoChange" accept="video/*" class="form-control" />
              <div v-if="form.movie_url" class="mt-2">
                <video :src="form.movie_url" controls style="max-width: 100%; max-height: 300px;"></video>
              </div>
            </div>
  
            <div class="mb-3">
              <label class="form-label">Poster (chọn file ảnh)</label>
              <input
                type="file"
                @change="handlePosterChange"
                accept="image/*"
                class="form-control"
                ref="posterInput"
              />
              <div v-if="form.poster" class="mt-2">
                <img :src="form.poster" alt="Poster preview" style="max-width: 200px; max-height: 300px;" />
              </div>
            </div>
  
            <button type="submit" class="btn btn-success me-2">Thêm phim</button>
            <button type="button" class="btn btn-secondary" @click="cancelAdd">Huỷ</button>
          </form>
        </div>
  
        <!-- Danh sách phim -->
        <div class="row">
          <!-- Số lượng phim được lọc -->
          <div class="mb-3">
            <strong>Tổng số phim:</strong> {{ filteredMovies.length }}
          </div>
          <MovieCardAdmin
            v-for="movie in filteredMovies"
            :key="movie._id"
            :movie="movie"
            @edit="handleEditMovie"
            @delete="handleDeleteMovie"
            @updated="fetchMovies"
          />
        </div>
  
        <div v-if="movies.length === 0" class="text-center text-muted">
          Không có phim nào để hiển thị.
        </div>
      </div>
  
      <AppFooter />
    </div>
  </template>
  
  <script>
  import AppHeader from "@/components/common/AppHeader.vue";
  import AppFooter from "@/components/common/AppFooter.vue";
  import MovieCardAdmin from "@/components/movies/movieCardAdmin.vue";
  import MovieService from "@/services/movie.service.js";
  
  export default {
    components: {
      AppHeader,
      AppFooter,
      MovieCardAdmin,
    },
    data() {
      return {
        movies: [],
        showAddForm: false,
        form: {
          name: "",
          duration: null,
          genre: [],
          director: "",
          actor: [],
          year_of_release: null,
          describe: "",
          movieFile: null,
          posterFile: null,
          movie_url: "",
          poster: "",
        },
        genreInput: "",
        actorInput: "",
        searchQuery: "",
      };
    },

    computed: {
      filteredMovies() {
        const removeVietnameseTones = (str) => {
          return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D");
        };

        const q = removeVietnameseTones(this.searchQuery.trim().toLowerCase());

        return this.movies.filter((movie) => {
          const movieName = removeVietnameseTones(movie.name.toLowerCase());
          return movieName.includes(q);
        }).reverse();
      },
    },
    
    methods: {
      async fetchMovies() {
        this.movies = await MovieService.getAll();
      },
      handleEditMovie(movie) {
        alert(`🛠 Chỉnh sửa phim: ${movie.name}`);
      },
      async handleDeleteMovie(id) {
        if (confirm("Bạn có chắc chắn muốn xoá phim này không?")) {
          const result = await MovieService.deleteMovie(id);
          if (result.status === "success") {
            alert("Đã xoá phim.");
            this.fetchMovies();
          } else {
            alert("Xoá thất bại: " + result.message);
          }
        }
      },
  
      handlePosterChange(event) {
        const file = event.target.files[0];
        if (!file) {
          this.form.poster = "";
          return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
          this.form.poster = e.target.result; // base64 string
        };
        reader.readAsDataURL(file);
        this.form.posterFile = file;
      },

      async uploadVideoFile(file) {
        const formData = new FormData();
        formData.append("file", file);

        // Giả sử backend có API upload riêng cho video
        const response = await fetch("http://127.0.0.1:8000/api/movie/uploadFiles", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) throw new Error("Upload video thất bại");

        const data = await response.json();
        return data.file_url;
      }, 
  
      async handleVideoChange(event) {
        const file = event.target.files[0];
        if (!file) {
          this.form.movieFile = null;
          this.form.movie_url = "";
          return;
        }
        this.form.movieFile = file;

        try {
          const url = await this.uploadVideoFile(file);
          this.form.movie_url = url; // Đường dẫn backend
        } catch (error) {
          alert("Lỗi upload video: " + error.message);
          this.form.movie_url = "";
        }
      },
  
      updateGenre() {
        this.form.genre = this.genreInput
          .split(",")
          .map((g) => g.trim())
          .filter((g) => g);
      },
      updateActor() {
        this.form.actor = this.actorInput
          .split(",")
          .map((a) => a.trim())
          .filter((a) => a);
      },
  
      cancelAdd() {
        this.showAddForm = false;
        this.resetForm();
      },
  
      resetForm() {
        this.form = {
          name: "",
          duration: null,
          genre: [],
          director: "",
          actor: [],
          year_of_release: null,
          describe: "",
          movieFile: null,
          posterFile: null,
          movie_url: "",
          poster: "",
        };
        this.genreInput = "";
        this.actorInput = "";
  
        // Reset input file cho poster
        if (this.$refs.posterInput) {
          this.$refs.posterInput.value = "";
        }
      },
  
      async handleSubmit() {
        // Cập nhật lại genre và actor trước khi gửi
        this.updateGenre();
        this.updateActor();
  
        try {
          const result = await MovieService.addMovie(this.form);
          if (result.status === "success") {
            alert(result.message);
            this.fetchMovies();
            this.cancelAdd();
          } else {
            alert("Thêm phim thất bại: " + result.message);
          }
        } catch (error) {
          alert("Lỗi khi thêm phim: " + error.message);
        }
      },
    },
    mounted() {
      this.fetchMovies();
    },
  };
  </script>
  
  <style scoped>
  .admin-container {
    padding: 40px 20px;
    max-width: 1200px;
    margin: auto;
    background-color: #ffffff;
  }
  </style>
  