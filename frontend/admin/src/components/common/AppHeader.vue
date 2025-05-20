<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark px-4">
    <router-link to="/" class="navbar-brand d-flex align-items-center">
      <i class="fas fa-film me-2"></i> PhimHay
    </router-link>
    <button
      class="navbar-toggler"
      type="button"
      data-bs-toggle="collapse"
      data-bs-target="#navbarContent"
    >
      <span class="navbar-toggler-icon"></span>
    </button>

    <div class="collapse navbar-collapse" id="navbarContent">
      <!-- Menu -->
      <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        <li class="nav-item">
          <router-link to="/" class="nav-link" active-class="active" exact>Trang chủ</router-link>
        </li>
        <li class="nav-item">
          <router-link to="#" class="nav-link" active-class="active">Tìm kiếm nâng cao</router-link>
        </li>
        <li class="nav-item" v-if="authStore.user?.position === 'admin'">
          <router-link to="/admin" class="nav-link" active-class="active">Quản lý Phim</router-link>
        </li>

      </ul>

      <!-- Kiểm tra trạng thái đăng nhập -->
      <div>
        <template v-if="authStore.isAuthenticated">
          <!-- User Dropdown Menu -->
          <div class="dropdown">
            <button 
              class="btn btn-primary border-0" 
              type="button" 
              id="userDropdown" 
              aria-expanded="false"
              @click="toggleDropdown"
            >
              <i class="fas fa-user-circle fa-lg"></i>
            </button>
            <ul 
              class="dropdown-menu dropdown-menu-end" 
              :class="{ show: isDropdownOpen }" 
              aria-labelledby="userDropdown"
            >
              <li class="dropdown-item text-muted">
                👤 Xin chào, <strong>{{ username }}</strong>
              </li>

              <li>
                <router-link :to="{ name: 'userdetail', params: { userId: authStore.user.id } }" class="dropdown-item">
                  <i class="fas fa-user"></i> Thông tin cá nhân
                </router-link>
              </li>

              <li>
                <router-link :to="{ name: 'historyrpage', params: { userId: authStore.user.id } }" class="dropdown-item text-primary">
                  <i class="fas fa-history"></i> Lịch sử xem
                </router-link>
              </li>

              <li>
                <router-link :to="{ name: 'favoriterpage', params: { userId: authStore.user.id } }" class="dropdown-item text-warning">
                  <i class="fas fa-star"></i> Phim ưa thích
                </router-link>
              </li>

              <li>
                <button @click="handleLogout" class="dropdown-item text-danger">
                  <i class="fas fa-sign-out-alt"></i> Đăng xuất
                </button>
              </li>
            </ul>
          </div>
        </template>
        
        <template v-else>
          <!-- Hiển thị "Đăng nhập / Đăng ký" nếu chưa đăng nhập -->
          <div class="auth-links">
            <router-link to="/login" class="auth-link">Đăng nhập</router-link>
            <span style="color: white;">/</span>
            <router-link to="/register" class="auth-link">Đăng ký</router-link>
          </div>
        </template>
      </div>
    </div>
  </nav>
</template>

<script>
import { computed, ref, onMounted, onBeforeUnmount } from "vue";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "vue-router";

export default {
  setup() {
    const authStore = useAuthStore();
    const router = useRouter();
    const isDropdownOpen = ref(false);

    // Lấy username từ store
    const username = computed(() => authStore.user?.name || "Người dùng");

    const toggleDropdown = () => {
      isDropdownOpen.value = !isDropdownOpen.value;
    };

    const closeDropdown = (event) => {
      // Đóng dropdown khi click bên ngoài
      if (isDropdownOpen.value && !event.target.closest('.dropdown')) {
        isDropdownOpen.value = false;
      }
    };

    const handleLogout = () => {
      authStore.logout();
      isDropdownOpen.value = false;
      router.push("/login"); // Chuyển hướng sau khi đăng xuất
    };

    // Xử lý sự kiện click ngoài dropdown để đóng nó
    onMounted(() => {
      document.addEventListener('click', closeDropdown);
    });

    onBeforeUnmount(() => {
      document.removeEventListener('click', closeDropdown);
    });

    return { 
      authStore, 
      username, 
      handleLogout,
      isDropdownOpen,
      toggleDropdown
    };
  },
};
</script>

<style scoped>
.navbar-brand {
  font-size: 1.5rem;
  font-weight: bold;
}

.auth-links {
  display: flex;
  align-items: center;
}

.auth-link {
  color: white;
  text-decoration: none;
}

.auth-link:hover {
  text-decoration: underline;
}
</style>
