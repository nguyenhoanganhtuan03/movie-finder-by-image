<template>
  <div class="col-12 mb-4">
    <div class="card flex-row h-100 shadow-sm">
      <!-- Ảnh poster -->
      <img
        :src="movie.poster || defaultPoster"
        class="img-fluid rounded-start"
        :alt="movie.name"
        style="width: 180px; height: 100%; object-fit: cover"
      />

      <!-- Nội dung bên phải -->
      <div class="card-body d-flex flex-column justify-content-between w-100">
        <div v-if="!isEditing">
          <h5 class="card-title mb-2">{{ movie.name }}</h5>
          <p class="card-text mb-1">⏱ Thời lượng: {{ movie.duration }} phút</p>
          <p class="card-text mb-3">
            📚 Thể loại:
            <span v-if="movie.genre && movie.genre.length">
              {{ movie.genre.join(", ") }}
            </span>
            <span v-else>Không rõ</span>
          </p>
          <p class="card-text mb-3 d-flex align-items-center gap-1">
            ⭐ Đánh giá:
            <span v-if="rating !== null">
            <span class="text-warning">
              <i
                v-for="n in 5"
                :key="n"
                class="bi"
                :class="n <= Math.round(rating) ? 'bi-star-fill' : 'bi-star'"
              ></i>
            </span>
            <small class="text-muted">({{ rating.toFixed(1) }} / 5)</small>
          </span>
          </p>
        </div>

        <!-- FORM chỉnh sửa -->
      <div v-else>
        <div class="mb-2">
          <label>Tên phim</label>
          <input v-model="formData.name" class="form-control form-control-sm" />
        </div>

        <div class="mb-2">
          <label>Thời lượng (phút)</label>
          <input v-model.number="formData.duration" type="number" class="form-control form-control-sm" />
        </div>

        <div class="mb-2">
          <label>Thể loại (phân cách bởi dấu phẩy)</label>
          <input v-model="formData.genre" class="form-control form-control-sm" />
        </div>

        <div class="mb-2">
          <label>Đạo diễn</label>
          <input v-model="formData.director" class="form-control form-control-sm" />
        </div>

        <div class="mb-2">
          <label>Diễn viên (phân cách bởi dấu phẩy)</label>
          <input v-model="formData.actor" class="form-control form-control-sm" />
        </div>

        <div class="mb-2">
          <label>Năm phát hành</label>
          <input v-model.number="formData.year_of_release" type="number" class="form-control form-control-sm" />
        </div>

        <div class="mb-2">
          <label>Mô tả</label>
          <textarea v-model="formData.describe" rows="2" class="form-control form-control-sm"></textarea>
        </div>

        <div class="mb-2">
          <label class="form-label">Chọn file video</label>
          <input type="file" @change="handleVideoChange" accept="video/*" class="form-control form-control-sm" />
          <div v-if="formData.movie_url" class="mt-2">
            <video :src="formData.movie_url" controls style="max-width: 100%; max-height: 250px;"></video>
          </div>
        </div>
        <div class="mb-2">
          <label class="form-label">Chọn ảnh poster</label>
          <input type="file" @change="handlePosterChange" accept="image/*" class="form-control form-control-sm" />
          <div v-if="formData.poster" class="mt-2">
            <img :src="formData.poster" alt="Poster preview" style="max-width: 200px; max-height: 300px;" />
          </div>
        </div>
      </div>
      
        <!-- Nút -->
        <div class="d-flex justify-content-end gap-2 mt-auto">
          <button v-if="!isEditing" class="btn btn-sm btn-primary" @click="handleWatchMovie">Xem phim</button>
          <button v-if="!isEditing" class="btn btn-sm btn-warning" @click="startEditing">Sửa</button>
          <button v-if="!isEditing" class="btn btn-sm btn-danger" @click="$emit('delete', movie._id)">Xoá</button>

          <!-- Nút khi đang sửa -->
          <template v-else>
            <button class="btn btn-sm btn-success" @click="submitUpdate">Lưu</button>
            <button class="btn btn-sm btn-secondary" @click="cancelEditing">Huỷ</button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import movieService from '@/services/movie.service';
import RatingService from "@/services/rating.service.js";


export default {
  name: "MovieCardAdmin",
  props: {
    movie: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      isEditing: false,
      rating: 0,
      formData: {
        name: "",
        duration: 0,
        genre: "",
        poster: "",
        director: "",
        actor: "",
        year_of_release: null,
        describe: "",
        movie_url: "",
        poster: "",
        movieFile: null,
        posterFile: null,
      },
    };
  },
  computed: {
    defaultPoster() {
      return "https://via.placeholder.com/250x350?text=No+Image";
    },
  },
  methods: {
    handleWatchMovie() {
      this.$router.push(`/movie/${this.movie._id}`);
    },
    async fetchRating() {
      try {
        const res = await RatingService.getRatingByMovieId(this.movie._id);
        this.rating = res.average_rating;
      } catch (error) {
        this.rating = "Lỗi";
        console.warn("Không lấy được rating:", error.message);
      }
    },
    startEditing() {
      this.isEditing = true;
      this.formData = {
        name: this.movie.name,
        duration: this.movie.duration,
        genre: this.movie.genre ? this.movie.genre.join(", ") : "",
        poster: this.movie.poster || "",
        director: this.movie.director,
        actor: this.movie.actor ? this.movie.actor.join(", ") : "",
        year_of_release: this.movie.year_of_release,
        describe: this.movie.describe,
        movie_url: this.movie.movie_url
      };
    },

    handlePosterChange(event) {
      const file = event.target.files[0];
      if (!file) {
        this.formData.poster = "";
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        this.formData.poster = e.target.result;
      };
      reader.readAsDataURL(file);
      this.formData.posterFile = file;
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
        this.formData.movieFile = null;
        this.formData.movie_url = "";
        return;
      }
      this.formData.movieFile = file;

      try {
        const url = await this.uploadVideoFile(file);
        this.formData.movie_url = url;
      } catch (error) {
        alert("Lỗi upload video: " + error.message);
        this.formData.movie_url = "";
      }
    },

    cancelEditing() {
      this.isEditing = false;
    },

    async submitUpdate() {
      const updatePayload = {
        name: this.formData.name,
        duration: this.formData.duration,
        genre: this.formData.genre.split(",").map(g => g.trim()),
        director: this.formData.director,
        actor: this.formData.actor.split(",").map(a => a.trim()),
        year_of_release: this.formData.year_of_release,
        describe: this.formData.describe,
        movie_url: this.formData.movie_url,
        poster: this.formData.poster,
      };

      try {
        const response = await movieService.updateMovie(this.movie._id, updatePayload);
        alert(response.message);
        this.$emit("updated");
        this.isEditing = false;
      } catch (err) {
        alert("Cập nhật thất bại!");
      }
    },
  },
  mounted() {
    this.fetchRating();
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
