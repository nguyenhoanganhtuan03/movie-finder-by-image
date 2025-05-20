<template>
  <div>
    <AppHeader />
    <div class="register-container">
      <div class="register-form">
        <h2>Đăng ký tài khoản</h2>

        <!-- Form đăng ký tài khoản -->
        <form @submit.prevent="handleRegister">
          <div class="mb-3">
            <label for="name" class="form-label">Tên tài khoản</label>
            <input
              type="text"
              id="name"
              v-model="name"
              class="form-control"
              required
              placeholder="Nhập tên tài khoản"
            />
          </div>

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
              placeholder="Nhập mật khẩu"
            />
          </div>

          <div class="mb-3">
            <label for="rePassword" class="form-label">Xác nhận mật khẩu</label>
            <input
              type="password"
              id="rePassword"
              v-model="rePassword"
              class="form-control"
              required
              placeholder="Nhập lại mật khẩu"
            />
          </div>

          <button type="submit" class="btn btn-primary w-100">Đăng ký</button>
        </form>

        <!-- Các nút đăng ký qua Gmail và Facebook -->
        <div class="social-login mt-3">
          <button @click="handleGoogleLogin" class="btn btn-danger w-48 mr-2">
            <i class="fab fa-google me-2"></i> Đăng ký với Google
          </button>
          <button @click="handleFacebookLogin" class="btn btn-primary w-48">
            <i class="fab fa-facebook me-2"></i> Đăng ký với Facebook
          </button>
        </div>

        <!-- Liên kết để chuyển sang trang đăng nhập -->
        <div class="mt-3 text-center">
          <span>Đã có tài khoản? </span>
          <router-link to="/login">Đăng nhập ngay</router-link>
        </div>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/store/auth";
import AppHeader from "@/components/common/AppHeader.vue";
import AppFooter from "@/components/common/AppFooter.vue";
import userService from "@/services/user.service";

export default {
  components: {
    AppHeader,
    AppFooter,
  },
  setup() {
    const router = useRouter();
    const authStore = useAuthStore();

    const name = ref("");
    const email = ref("");
    const password = ref("");
    const rePassword = ref("");

    const handleRegister = async () => {
      if (password.value !== rePassword.value) {
        alert("Mật khẩu không khớp, vui lòng thử lại.");
        return;
      }

      const userData = {
        name: name.value,
        email: email.value,
        password: password.value,
      };

      const response = await userService.register(userData);

      if (response.status === "success") {
        alert(response.message);
        router.push("/login");
      } else {
        alert(response.message || "Đăng ký thất bại. Vui lòng kiểm tra lại thông tin.");
      }
    };

    const handleGoogleLogin = () => {
      alert("Đăng ký với Google chưa được tích hợp.");
    };

    const handleFacebookLogin = () => {
      alert("Đăng ký với Facebook chưa được tích hợp.");
    };

    return {
      name,
      email,
      password,
      rePassword,
      handleRegister,
      handleGoogleLogin,
      handleFacebookLogin,
    };
  },
};
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: flex-start; /* form nằm sát phía trên */
  padding-top: 40px;
  padding-bottom: 60px;
  background-color: #f8f9fa;
}

.register-form {
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

.social-login button {
  display: inline-block;
  width: 48%;
  margin-left: 1%;
  margin-right: 1%;
}

.social-login button i {
  font-size: 1.2rem;
}

.mt-3 {
  margin-top: 1rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.text-center {
  text-align: center;
}

.text-center a {
  color: #007bff;
}

.text-center a:hover {
  text-decoration: underline;
}
</style>
