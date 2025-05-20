<template>
  <div>
    <!-- Header -->
    <AppHeader />

    <div class="login-container">
      <div class="login-form">
        <h2>Đăng nhập</h2>

        <!-- Form đăng nhập -->
        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <label for="email" class="form-label">Email</label>
            <input
              type="email"
              id="email"
              v-model="email"
              class="form-control"
              required
              placeholder="Nhập email của bạn"
            />
          </div>

          <div class="mb-3">
            <label for="password" class="form-label">Mật khẩu</label>
            <input
              type="password"
              id="password"
              v-model="password"
              class="form-control"
              required
              placeholder="Nhập mật khẩu của bạn"
            />
          </div>

          <button type="submit" class="btn btn-primary w-100">Đăng nhập</button>
        </form>

        <!-- Các nút đăng nhập qua Gmail và Facebook -->
        <div class="social-login mt-3">
          <button @click="handleGoogleLogin" class="btn btn-danger w-48 mr-2">
            <i class="fab fa-google me-2"></i> Đăng nhập với Google
          </button>
          <button @click="handleFacebookLogin" class="btn btn-primary w-48">
            <i class="fab fa-facebook me-2"></i> Đăng nhập với Facebook
          </button>
        </div>

        <!-- Liên kết chuyển sang đăng ký -->
        <div class="mt-3 text-center">
          <span>Chưa có tài khoản? </span>
          <router-link to="/register">Đăng ký ngay</router-link>
        </div>

        <div class="mt-3 text-center">
            <router-link to="/stafflogin">Đăng nhập với tư cách nhân viên</router-link>
          </div>

      </div>
    </div>

    <!-- Footer -->
    <AppFooter />
  </div>
</template>

<script>
import { ref } from "vue";
import { useRouter } from "vue-router";
import userService from "@/services/user.service";
import { useAuthStore } from "@/store/auth";
import AppHeader from "@/components/common/AppHeader.vue";
import AppFooter from "@/components/common/AppFooter.vue";

export default {
  components: {
    AppHeader,
    AppFooter,
  },
  setup() {
    const authStore = useAuthStore();
    const router = useRouter();
    const email = ref("");
    const password = ref("");
    const errorMessage = ref("");
    const loading = ref(false);

    const handleLogin = async () => {
      errorMessage.value = "";
      loading.value = true;

      try {
        const response = await userService.login({
          email: email.value,
          password: password.value,
        });

        if (response.status === "success") {
          authStore.login(response.user);
          alert("🎉 Đăng nhập thành công!");
          router.push("/");
        } else {
          errorMessage.value = response.message;
        }
      } catch (error) {
        console.error("🔴 Login error:", error);
        errorMessage.value = "Lỗi đăng nhập, vui lòng thử lại!";
      }

      loading.value = false;
    };

    return {
      email,
      password,
      errorMessage,
      loading,
      handleLogin,
    };
  },
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 40px;
  padding-bottom: 60px;
  background-color: #f8f9fa;
}

.login-form {
  background-color: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 800px;
}

h2 {
  text-align: center;
  margin-bottom: 20px;
}

.social-login {
  display: flex;
  justify-content: space-between;
}

.social-login button {
  width: 48%;
}

.text-center a {
  color: #007bff;
}

.text-center a:hover {
  text-decoration: underline;
}
</style>
