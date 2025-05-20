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
import { defineComponent, ref, watch } from "vue";
import { useAuthStore } from "@/store/auth";
import FavoriteService from "@/services/favorite.service";
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

    // Cập nhật videoSrc khi props.movie thay đổi
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

    const handleAddToFavorites = async () => {
      if (!authStore.isLoggedIn) {
        alert("Vui lòng đăng nhập để thêm vào yêu thích.");
        router.push("/login");
        return;
      }

      try {
        const userId = authStore.user?.id;
        const movieId = route.params.movieId;

        console.log("🧩 userId:", userId);
        console.log("🎬 movieId:", movieId);

        if (!movieId) {
          alert("Không tìm thấy movie_id trong URL.");
          return;
        }

        const result = await FavoriteService.addToFavorites(userId, movieId);
        console.log(result);

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
