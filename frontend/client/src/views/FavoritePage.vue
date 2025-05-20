<template>
  <div>
    <AppHeader />

    <div class="container mt-4">
      <h3 class="mb-4">🎬 Danh sách yêu thích</h3>

      <div v-if="loading">Đang tải dữ liệu...</div>
      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-else-if="favoriteWithMovies.length === 0">Không có phim yêu thích nào.</div>
      <div v-else>
        <div class="row">
          <FavoriteCard
            v-for="(item, index) in displayedFavorites"
            :key="item._id"
            :movie="item.movie"
            :favoriteId="item._id"
            :show-delete="true"
            @favorite-deleted="removeFavorite"
          />
        </div>

        <div v-if="favorites.length > 4" class="text-center mt-4">
          <button class="btn btn-primary" @click="showMore = !showMore">
            {{ showMore ? "Thu gọn" : "Xem thêm" }}
          </button>
        </div>
      </div>
    </div>

    <AppFooter />
  </div>
</template>

<script>
import { onMounted, ref, computed } from "vue";
import FavoriteService from "@/services/favorite.service.js";
import MovieService from "@/services/movie.service.js";
import AppHeader from "@/components/common/AppHeader.vue";
import AppFooter from "@/components/common/AppFooter.vue";
import FavoriteCard from "@/components/favorites/favoriteCard.vue";
import { useAuthStore } from "@/store/auth";

export default {
  name: "FavoritePage",
  components: {
    AppHeader,
    AppFooter,
    FavoriteCard,
  },
  setup() {
    const authStore = useAuthStore();
    const userId = authStore.user?.id || null;

    const favorites = ref([]);
    const loading = ref(false);
    const error = ref(null);
    const showMore = ref(false);

    // Tạo mảng chứa object { _id: favoriteId, movie: fullMovieData }
    const favoriteWithMovies = ref([]);

    const displayedFavorites = computed(() => {
      const reversed = [...favoriteWithMovies.value].reverse();
      return showMore.value ? reversed : reversed.slice(0, 4);
    });

    onMounted(async () => {
      if (!userId) {
        error.value = "Bạn chưa đăng nhập.";
        return;
      }

      loading.value = true;
      try {
        const result = await FavoriteService.getFavoritesByUserId(userId);
        console.log("🔥 Favorite raw result:", result);  // Thêm dòng này

        favorites.value = result;

        const moviePromises = result.map((item) =>
          MovieService.getById(item.movie_id)
        );

        const movies = await Promise.all(moviePromises);

        favoriteWithMovies.value = result.map((fav, index) => {
          console.log("Mapping favorite:", fav);  // Thêm dòng này
          return {
            _id: fav._id,  // <-- kiểm tra có _id hay không
            movie: movies[index],
          };
        });

        console.log("Mapped favoriteWithMovies:", favoriteWithMovies.value); // Thêm dòng này

      } catch (err) {
        error.value = err.message || "Lỗi không xác định";
        console.error("Lỗi khi tải danh sách yêu thích:", err);
      } finally {
        loading.value = false;
      }
    });

    function removeFavorite(favoriteId) {
      favoriteWithMovies.value = favoriteWithMovies.value.filter(
        (fav) => fav._id !== favoriteId
      );
    }

    return {
      favorites,
      favoriteWithMovies,
      displayedFavorites,
      loading,
      error,
      showMore,
      removeFavorite,
    };
  },
};
</script>
