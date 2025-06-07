<template>
  <div class="container mt-4">
    <div class="card shadow-sm p-4">
      <h2 class="mb-3 text-primary text-center">{{ movie.name }}</h2>

      <!-- Video -->
      <div class="video-container mb-4">
        <strong>Xem phim:</strong>
        <video
          v-if="videoSrc"
          :src="videoSrc"
          class="video-player mt-2"
          controls
        >
          Trình duyệt của bạn không hỗ trợ thẻ video.
        </video>
        <p v-else class="text-muted mt-2">Không có URL video để hiển thị.</p>
      </div>

      <!-- Movie info -->
      <div class="row g-3 mb-4">
        <div class="col-md-6"><strong>Thời lượng:</strong> {{ movie.duration }} phút</div>
        <div class="col-md-6"><strong>Thể loại:</strong> {{ movie.genre.join(', ') }}</div>
        <div class="col-md-6"><strong>Đạo diễn:</strong> {{ movie.director }}</div>
        <div class="col-md-6"><strong>Diễn viên:</strong> {{ movie.actor.join(', ') }}</div>
        <div class="col-md-6"><strong>Năm phát hành:</strong> {{ movie.year_of_release }}</div>

        <!-- Phần đánh giá -->
        <div class="col-md-6">
          <div class="d-flex align-items-center flex-wrap mb-2">
            <strong class="me-2">Đánh giá:</strong>

            <div
              class="d-flex align-items-center text-warning"
              style="cursor: pointer;"
              @mouseleave="hoverRating = 0"
              role="group"
              aria-label="Star rating"
            >
              <i
                v-for="n in 5"
                :key="n"
                class="bi"
                :class="{
                  'bi-star-fill': n <= (hoverRating || Math.round(rating)),
                  'bi-star': n > (hoverRating || Math.round(rating)),
                  'text-warning': true,
                }"
                @mouseenter="hoverRating = n"
                @click="submitRating(n)"
                :aria-pressed="n === selectedRating"
                tabindex="0"
                @keydown.enter.prevent="submitRating(n)"
                @keydown.space.prevent="submitRating(n)"
              ></i>
            </div>

            <small class="text-muted ms-2" v-if="rating !== null">
              ({{ rating.toFixed(1) }} / 5)
            </small>
            <span v-else class="text-muted ms-2">Chưa có đánh giá</span>
          </div>
        </div>

        <div class="col-12"><strong>Mô tả:</strong> {{ movie.describe }}</div>
      </div>

      <!-- Favorite button -->
      <div class="text-center mb-3">
        <button class="btn btn-danger" @click="handleAddToFavorites">
          ❤️ Thêm vào yêu thích
        </button>
      </div>

      <div class="text-center">
        <router-link to="/" class="btn btn-secondary">⬅ Quay về trang chính</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, watch, onMounted } from "vue";
import { useAuthStore } from "@/store/auth";
import FavoriteService from "@/services/favorite.service";
import RatingService from "@/services/rating.service";
import { useRouter, useRoute } from "vue-router";

export default defineComponent({
  name: "MovieDetail",
  props: {
    movie: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    const authStore = useAuthStore();
    const router = useRouter();
    const route = useRoute();

    const videoSrc = ref(null);

    watch(
      () => props.movie,
      (newMovie) => {
        if (!newMovie || !newMovie.movie_url) {
          videoSrc.value = null;
        } else if (newMovie.movie_url instanceof Blob || newMovie.movie_url instanceof File) {
          videoSrc.value = URL.createObjectURL(newMovie.movie_url);
        } else if (typeof newMovie.movie_url === "string") {
          videoSrc.value = newMovie.movie_url;
        } else {
          videoSrc.value = null;
        }
      },
      { immediate: true }
    );

    const rating = ref(null);
    const hoverRating = ref(0);
    const selectedRating = ref(0); // lưu đánh giá user vừa chọn

    const loadRating = async () => {
      try {
        const res = await RatingService.getRatingByMovieId(props.movie._id);
        rating.value = res.average_rating;
      } catch (error) {
        rating.value = null;
        console.warn("⚠️ Không có rating cho phim này:", error?.response?.data?.detail || error.message);
      }
    };

    onMounted(() => {
      loadRating();
    });

    const submitRating = async (score) => {
      if (!authStore.isLoggedIn) {
        alert("Vui lòng đăng nhập để đánh giá phim.");
        router.push("/login");
        return;
      }

      try {
        await RatingService.addRatingScore(props.movie._id, score);
        alert(`Cảm ơn bạn đã đánh giá ${score} sao!`);
        selectedRating.value = score;
        hoverRating.value = 0;
        await loadRating();
      } catch (error) {
        console.error("❌ Lỗi khi gửi đánh giá:", error);
        alert("Có lỗi xảy ra khi gửi đánh giá.");
      }
    };

    const handleAddToFavorites = async () => {
      if (!authStore.isLoggedIn) {
        alert("Vui lòng đăng nhập để thêm vào yêu thích.");
        router.push("/login");
        return;
      }

      try {
        const userId = authStore.user?.id;
        const movieId = route.params.movieId;

        if (!movieId) {
          alert("Không tìm thấy movie_id trong URL.");
          return;
        }

        const result = await FavoriteService.addToFavorites(userId, movieId);

        if (result.message === "Movie is already in the favorites list") {
          alert("🎬 Bộ phim đã có trong danh sách yêu thích.");
        } else {
          alert("🎉 Đã thêm vào danh sách yêu thích!");
        }
      } catch (error) {
        console.error("❌ Lỗi khi thêm vào yêu thích:", error);
        alert("Có lỗi xảy ra khi thêm vào yêu thích.");
      }
    };

    return {
      movie: props.movie,
      videoSrc,
      handleAddToFavorites,
      rating,
      hoverRating,
      selectedRating,
      submitRating,
    };
  },
});
</script>

<style scoped>
.container {
  max-width: 900px;
}

.video-player {
  width: 100%;
  max-height: 450px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: black;
}

.video-container {
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 1rem;
}
</style>
