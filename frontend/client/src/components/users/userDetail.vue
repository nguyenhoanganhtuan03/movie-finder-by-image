<template>
    <div class="user-detail-container" v-if="user">
      <h2>Thông tin người dùng</h2>
  
      <div class="info-group">
        <label>Tên người dùng:</label>
        <p>{{ user.name }}</p>
      </div>
  
      <div class="info-group">
        <label>Email:</label>
        <p>{{ user.email }}</p>
      </div>
  
      <div class="info-group">
        <label>Mật khẩu:</label>
        <p>********</p>
      </div>
  
      <div class="button-group">
        <button class="btn btn-warning" @click="showChangePassword = !showChangePassword">
          {{ showChangePassword ? 'Ẩn đổi mật khẩu' : 'Đổi mật khẩu' }}
        </button>
        <button class="btn btn-danger" @click="confirmDelete">Xóa tài khoản</button>
      </div>
  
      <!-- 🔐 Form đổi mật khẩu -->
      <div v-if="showChangePassword" class="password-form">
        <h3>Đổi mật khẩu</h3>
        <input type="password" v-model="passwordData.old_password" placeholder="Mật khẩu hiện tại" />
        <input type="password" v-model="passwordData.new_password" placeholder="Mật khẩu mới" />
        <button class="btn btn-success" @click="handleChangePassword">Xác nhận</button>
      </div>
    </div>
  
    <div v-else class="loading">
      Đang tải thông tin người dùng...
    </div>
  </template>
  
  <script>
  import UserService from "@/services/user.service";
  import { useAuthStore } from "@/store/auth";
  
  export default {
    name: "UserDetail",
    data() {
      return {
        user: null,
        showChangePassword: false,
        passwordData: {
          old_password: "",
          new_password: "",
        },
        error: null,
      };
    },
    async mounted() {
      const userId = this.$route.params.userId;
      try {
        const res = await UserService.getUserById(userId);
        if (res.status === "success") {
          this.user = res.user;
        } else {
          this.error = res.message || "Không thể lấy thông tin người dùng.";
        }
      } catch (err) {
        this.error = "Lỗi khi gọi API: " + err.message;
      }
    },
    methods: {
      async handleChangePassword() {
        if (!this.passwordData.old_password || !this.passwordData.new_password) {
          alert("Vui lòng điền đầy đủ thông tin.");
          return;
        }
  
        const res = await UserService.updatePassword(this.user._id, this.passwordData);
        if (res.status === "success") {
          alert("Đổi mật khẩu thành công.");
          this.passwordData.old_password = "";
          this.passwordData.new_password = "";
          this.showChangePassword = false;
        } else {
          alert("Lỗi: " + res.message);
        }
      },
  
        async confirmDelete() {
        const confirmed = confirm("Bạn có chắc chắn muốn xóa tài khoản?");
        if (confirmed) {
            const res = await UserService.deleteUser(this.user._id);
            if (res.status === "success") {
            alert("Tài khoản đã được xóa.");

            // 🔐 Gọi logout từ Pinia store
            const authStore = useAuthStore();
            authStore.logout();

            // Chuyển về trang đăng nhập
            this.$router.push("/login");
            } else {
            alert("Xóa thất bại: " + res.message);
            }
        }
        },
    }
  };
  </script>
  
  <style scoped>
  .user-detail-container {
    max-width: 500px;
    margin: 50px auto;
    padding: 30px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  }
  
  h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  
  .info-group {
    margin-bottom: 15px;
  }
  
  .info-group label {
    font-weight: bold;
    display: block;
  }
  
  .button-group {
    display: flex;
    justify-content: space-between;
    margin-top: 20px;
  }
  
  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    color: white;
    cursor: pointer;
  }
  
  .btn-warning {
    background-color: #f0ad4e;
  }
  
  .btn-danger {
    background-color: #d9534f;
  }
  
  .btn-success {
    background-color: #5cb85c;
    margin-top: 10px;
    width: 100%;
  }
  
  .password-form {
    margin-top: 20px;
  }
  
  .password-form input {
    width: 100%;
    padding: 10px;
    margin-bottom: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  
  .loading {
    max-width: 500px;
    margin: 50px auto;
    padding: 30px;
    text-align: center;
    font-style: italic;
    color: #777;
  }
  </style>
  