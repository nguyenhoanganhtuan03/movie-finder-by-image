<template>
    <div>
      <!-- Header -->
      <AppHeader />
  
      <div class="login-container">
        <div class="login-form">
          <h2>Đăng nhập nhân viên</h2>
  
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
                placeholder="Nhập email nhân viên"
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
  
            <button type="submit" class="btn btn-primary w-100">
              Đăng nhập nhân viên
            </button>
          </form>
  
          <!-- Hiển thị lỗi nếu có -->
          <div v-if="errorMessage" class="text-danger mt-3 text-center">
            {{ errorMessage }}
          </div>
  
          <!-- Liên kết quay lại trang người dùng -->
          <div class="mt-3 text-center">
            <router-link to="/login">Đăng nhập với tư cách người dùng</router-link>
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
  import staffService from "@/services/staff.service";
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
            const response = await staffService.Stafflogin({
            email: email.value,
            password: password.value,
            });

            if (response.status === "success") {
            authStore.login(response.user);
            alert("🎉 Đăng nhập nhân viên thành công!");

            // 🔹 Chuyển hướng nếu là admin
            if (response.user.position === "admin") {
                router.push("/admin");
            }
            } else {
            errorMessage.value = response.message;
            }
        } catch (error) {
            console.error("🔴 Staff login error:", error);
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
    max-width: 600px;
  }
  
  h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  
  .text-center a {
    color: #007bff;
  }
  
  .text-center a:hover {
    text-decoration: underline;
  }
  </style>
  