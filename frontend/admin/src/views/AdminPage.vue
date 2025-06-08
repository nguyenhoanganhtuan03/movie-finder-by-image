<template>
    <div>
      <AppHeader />
  
      <div class="admin-container">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2>Quản lý phim</h2>
          <div class="d-flex align-items-center mb-3">
            <button class="btn btn-primary" @click="showAddForm = true">+ Thêm phim</button>
            <button class="btn btn-outline-primary ms-2" @click="showBulkForm = true">📂 Thêm hàng loạt</button>
          </div>

          <!-- Modal thêm hàng loạt -->
          <div v-if="showBulkForm" class="modal-backdrop">
            <div class="modal-content-custom">
              <h4 class="mb-3">📋 Thêm phim hàng loạt từ Excel</h4>
              
              <div class="alert alert-warning mb-3" role="alert" style="font-size: 0.9rem;">
                ⚠️ Lưu ý: Chưa thể thêm video và poster trong upload hàng loạt, vui lòng thêm sau.
              </div>

              <div class="mb-3">
                <a :href="excelTemplateUrl" download class="btn btn-link">📥 Tải file mẫu Excel</a>
              </div>

              <div class="mb-3">
                <label class="form-label">Chọn file Excel (.xlsx)</label>
                <input type="file" @change="handleExcelUpload" accept=".xlsx" class="form-control" />
              </div>

              <div class="d-flex justify-content-end mt-3">
                <button class="btn btn-secondary me-2" @click="showBulkForm = false">Hủy</button>
              </div>
            </div>
          </div>
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
  import RatingService from "@/services/rating.service.js";
  import * as XLSX from "xlsx";
  
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
        showBulkForm: false,
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
        excelTemplateUrl: "/movies_data.xlsx",
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
          this.form.poster = e.target.result;
        };
        reader.readAsDataURL(file);
        this.form.posterFile = file;
      },
  
      async uploadVideoFile(file) {
        const formData = new FormData();
        formData.append("file", file);
  
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
          this.form.movie_url = url;
        } catch (error) {
          alert("Lỗi upload video: " + error.message);
          this.form.movie_url = "";
        }
      },
  
      updateGenre() {
        this.form.genre = this.genreInput.split(",").map((g) => g.trim()).filter((g) => g);
      },
  
      updateActor() {
        this.form.actor = this.actorInput.split(",").map((a) => a.trim()).filter((a) => a);
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
  
        if (this.$refs.posterInput) {
          this.$refs.posterInput.value = "";
        }
      },
  
      async handleSubmit() {
        this.updateGenre();
        this.updateActor();
  
        const result = await MovieService.addMovie(this.form);
        if (result.status === "success") {
          alert(result.message);
          try {
            const movieId = result.data?._id;
            if (movieId) {
              await RatingService.createRating(movieId, 5);
            }
          } catch (err) {
            console.warn("⚠️ Không thể tạo rating:", err.message);
          }

          this.fetchMovies();
          this.cancelAdd();
        } else {
          alert("Thêm phim thất bại: " + result.message);
        }
      },
  
      // ✅ Xử lý upload file Excel
      async handleExcelUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
  
        try {
          const data = await file.arrayBuffer();
          const workbook = XLSX.read(data);
          const sheet = workbook.Sheets[workbook.SheetNames[0]];
          const rows = XLSX.utils.sheet_to_json(sheet);
          console.log("📄 Dữ liệu đọc từ Excel:", rows);
  
          for (const row of rows) {
            const movie = {
              name: row["Tên phim"] || "",
              duration: Number(row["Thời lượng"]) || null,
              genre: (row["Thể loại"] || "").split(/\s*,\s*/).map(g => g.trim()).filter(g => g),
              director: row["Đạo diễn"] || "",
              actor: (row["Diễn viên"] || "").split(/\s*,\s*/).map(a => a.trim()).filter(a => a),
              year_of_release: Number(row["Năm phát hành"]) || null,
              describe: row["Mô tả"] || "",
              movieFile: null,
              posterFile: null,
              movie_url: "",
              poster: "",
            };
  
            if (!movie.name || !movie.duration) continue;
  
            try {
              const result = await MovieService.addMovie(movie);
              if (result.status === "success") {
                const movieId = result.data?._id;
                if (movieId) {
                  try {
                    await RatingService.createRating(movieId, 5);
                  } catch (ratingErr) {
                    console.warn(`⚠️ Không thể tạo rating cho "${movie.name}":`, ratingErr.message);
                  }
                }
              } else {
                console.warn("Thêm thất bại:", result.message);
              }
            } catch (err) {
              console.error("❌ Lỗi thêm phim từ Excel:", err.message);
            }
          }

          alert("✅ Đã xử lý xong file Excel.");
          this.fetchMovies();
        } catch (error) {
          alert("Lỗi đọc file Excel: " + error.message);
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

  .modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5); /* nền mờ */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

.modal-content-custom {
  background-color: white;
  padding: 30px;
  border-radius: 10px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.25);
}

  </style>
  