<template>
  <div>
    <AppHeader />

    <div class="container my-5">
      <h2 class="mb-4 text-center">Tìm kiếm phim</h2>

      <!-- Chia 2 phần -->
      <div class="d-flex flex-wrap gap-4">
        <!-- BÊN TRÁI: Nhập mô tả, upload ảnh, upload video -->
        <div class="flex-grow-1" style="min-width: 280px;">
          <!-- Nhập mô tả -->
          <div class="mb-3">
            <label class="form-label">Nhập mô tả ngắn gọn:</label>
            <input
              v-model="searchText"
              type="text"
              class="form-control"
              placeholder="Vui lòng nhập mô tả rõ ràng để có thể tìm kiếm chính xác hơn"
              @keyup.enter="searchByContent"
            />
          </div>

          <!-- Upload ảnh -->
          <div class="mb-3">
            <label class="form-label">Tải lên ảnh:</label>
            <input 
              ref="imageInput"
              type="file" 
              accept="image/jpeg,image/jpg,image/png" 
              @change="handleImageUpload" 
              class="form-control" 
            />
          </div>

          <!-- Upload video -->
          <div class="mb-3">
            <label class="form-label">Tải lên video (MP4):</label>
            <input 
              ref="videoInput"
              type="file" 
              accept="video/mp4,video/mov" 
              @change="handleVideoUpload" 
              class="form-control" 
            />
          </div>

          <!-- Upload âm thanh -->
          <div class="mb-3">
            <label class="form-label">Tải lên file âm thanh (MP3/WAV):</label>
            <input 
              ref="audioInput"
              type="file" 
              accept="audio/mpeg,audio/wav" 
              @change="handleAudioUpload" 
              class="form-control" 
            />
          </div>
          <div v-if="isUploading" class="mt-2">
              <span class="text-info">Đang xử lý...</span>
          </div>
        </div>

        <!-- BÊN PHẢI: Ngưỡng tương đồng -->
        <div style="min-width: 200px;">
          <!-- Ngưỡng cho ảnh -->
          <div class="mb-3">
            <label class="form-label">Ngưỡng tương đồng:</label>
            <select v-model.number="similarityThreshold" class="form-select">
              <option v-for="n in 11" :key="'img-' + n" :value="(n - 1) * 0.1">
                {{ ((n - 1) * 0.1).toFixed(1) }}
              </option>
            </select>
          </div>

          <!-- Chọn số lượng phim hiển thị -->
          <div class="mb-3">
            <label class="form-label">Số lượng tìm kiếm tối đa:</label>
            <select v-model.number="resultLimit" class="form-select">
              <option v-for="n in 20" :key="'limit-' + n" :value="n">
                {{ n }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Lưu ý chung -->
      <div class="alert alert-warning w-100 mt-3 text-center" role="alert">
        ⚠️ File video và âm thanh hoạt động tốt nhất với thời lượng từ <strong>30 giây đến 10 phút</strong>.
      </div>

      <!-- Video preview nếu có -->
      <div v-if="videoURL" class="d-flex align-items-center justify-content-center mt-3 gap-3 flex-wrap">
        <video :src="videoURL" controls style="max-width: 100%; max-height: 300px;"></video>
        <button @click="clearVideo" class="btn btn-sm btn-secondary">Xóa video</button>
      </div>

      <!-- Ảnh preview nếu có -->
      <div v-if="imageURL" class="d-flex align-items-center justify-content-center mt-3 gap-3 flex-wrap">
        <img :src="imageURL" alt="Ảnh upload" style="max-width: 100%; max-height: 300px;" />
        <button @click="clearImage" class="btn btn-sm btn-secondary">Xóa ảnh</button>
      </div>

      <!-- Âm thanh preview nếu có -->
      <div v-if="audioURL" class="d-flex align-items-center justify-content-center mt-3 gap-3 flex-wrap">
        <div class="d-flex flex-column align-items-center">
          <audio :src="audioURL" controls style="max-width: 100%;"></audio>
          <small class="text-muted mt-1">{{ audioName }}</small>
        </div>
        <button @click="clearAudio" class="btn btn-sm btn-secondary">Xóa âm thanh</button>
      </div>

      <!-- Hiển thị tên phim được dự đoán -->
      <div v-if="predictedName" class="alert alert-info mt-3">
        <strong>Phim được tìm thấy:</strong> {{ predictedName }}
      </div>

      <hr />

      <!-- Kết quả -->
      <h5 class="mt-4">Kết quả tìm kiếm:</h5>
      <div class="row">
        <MovieCard
          v-for="movie in searchResults"
          :key="movie._id"
          :movie="movie"
        />
      </div>

      <div v-if="searchResults.length === 0 && !isUploading" class="text-muted mt-3">
        Không tìm thấy kết quả nào.
      </div>
    </div>

    <!-- Nút bật chatbot -->
    <button
        v-if="!isChatOpen"
        @click="isChatOpen = true"
        class="btn btn-primary rounded-circle shadow-lg"
        style="position: fixed; bottom: 24px; right: 24px; width: 60px; height: 60px; z-index: 9999;"
      >
        <i class="bi bi-robot fs-4"></i>
      </button>

    <!-- Chatbot widget -->
    <MiniChatWidget v-if="isChatOpen" @close="isChatOpen = false" />

    <AppFooter />
  </div>
</template>

<script>
import AppHeader from "@/components/common/AppHeader.vue";
import AppFooter from "@/components/common/AppFooter.vue";
import MovieCard from "@/components/movies/movieCard.vue";
import MovieService from "@/services/movie.service";
import FinderService from "@/services/finder.service";
import MiniChatWidget from "@/components/chatbot/ChatbotWidget.vue";

export default {
  components: {
    AppHeader,
    AppFooter,
    MovieCard,
    MiniChatWidget,
  },
  data() {
      return {
      searchText: "",
      videoURL: "",
      imageURL: "",
      audioURL: "",
      searchResults: [],
      predictedName: "",
      isUploading: false,
      isChatOpen: false,
      similarityThreshold: 0.8,
      resultLimit: 6
    };
  },
  methods: {
    async searchByContent() {
      const text = this.searchText.trim();
      if (!text) {
        this.searchResults = [];
        this.predictedName = "";
        return;
      }

      try {
        const result = await FinderService.searchByContent(text, this.similarityThreshold, this.resultLimit); 

        this.searchResults = result.results || [];
        this.predictedName = result.predicted_name || "";

        if (this.searchResults.length === 0) {
          alert("Không tìm kiếm được phim từ mô tả này!");
        }
      } catch (error) {
        console.error("Lỗi khi tìm kiếm theo nội dung:", error);
        this.searchResults = [];
        this.predictedName = "";
      }
    },

    async handleAudioUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const allowedTypes = ['audio/mpeg', 'audio/wav'];
      if (!allowedTypes.includes(file.type)) {
        alert("Chỉ chấp nhận file âm thanh MP3 hoặc WAV!");
        this.clearAudioInput();
        return;
      }

      this.audioURL = URL.createObjectURL(file);
      this.audioName = file.name;

      if (file.size > 50 * 1024 * 1024) {
        alert("Kích thước file quá lớn! Vui lòng chọn file dưới 50MB.");
        this.clearAudioInput();
        return;
      }

      const audio = document.createElement("audio");
      audio.preload = "metadata";

      audio.onloadedmetadata = async () => {
        const duration = audio.duration;

        if (duration < 30 || duration > 600) {
          alert("Thời lượng âm thanh phải từ 30 giây đến 10 phút!");
          this.clearAudioInput();
          return;
        }

        try {
          this.isUploading = true;
          this.clearImage();
          this.clearVideo();

          const result = await FinderService.searchByAudio(file, this.similarityThreshold, this.resultLimit);
          this.searchResults = result.results || [];
          this.predictedName = result.predicted_name || "";

          if (this.searchResults.length === 0) {
            alert("Không nhận diện được phim từ âm thanh này!");
          }
        } catch (error) {
          console.error("Lỗi upload audio:", error);
          alert("Có lỗi xảy ra khi xử lý âm thanh!");
        } finally {
          this.isUploading = false;
        }
      };

      audio.onerror = () => {
        alert("Không thể đọc được file âm thanh!");
        this.clearAudioInput();
      };

      audio.src = URL.createObjectURL(file);
    },

    async handleImageUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
      if (!allowedTypes.includes(file.type)) {
        alert("Chỉ chấp nhận file ảnh định dạng JPG, JPEG, PNG!");
        this.clearImageInput();
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        alert("Kích thước ảnh quá lớn! Vui lòng chọn ảnh dưới 10MB.");
        this.clearImageInput();
        return;
      }

      try {
        this.isUploading = true;
        this.clearVideo(); // Xóa video nếu có
        this.imageURL = URL.createObjectURL(file);
        
        const result = await MovieService.searchByFile(file, this.similarityThreshold, this.resultLimit);
        this.searchResults = result.results || [];
        this.predictedName = result.predicted_name || "";
        console.log(result.results)

        if (this.searchResults.length === 0) {
          alert("Không nhận diện được phim từ ảnh này!");
        }
      } catch (error) {
        console.error("Lỗi upload ảnh:", error);
        alert("Có lỗi xảy ra khi xử lý ảnh!");
        this.clearImage();
      } finally {
        this.isUploading = false;
      }
    },

    async handleVideoUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const allowedTypes = ['video/mp4', 'video/mov'];
      if (!allowedTypes.includes(file.type)) {
        alert("Chỉ chấp nhận file video định dạng MP4, MOV!");
        this.clearVideoInput();
        return;
      }

      if (file.size > 50 * 1024 * 1024) {
        alert("Kích thước video quá lớn! Vui lòng chọn video dưới 50MB.");
        this.clearVideoInput();
        return;
      }

      const video = document.createElement("video");
      video.preload = "metadata";
      
      video.onloadedmetadata = async () => {
        try {
          const duration = video.duration;

          if (duration < 30 || duration > 600) {
            alert("Video phải có thời lượng từ 30 giây đến 10 phút!");
            this.clearVideoInput();
            return;
          }

          this.isUploading = true;
          this.clearImage(); // Xóa ảnh nếu có
          this.videoURL = URL.createObjectURL(file);
          
          const result = await MovieService.searchByFile(file, this.similarityThreshold, this.resultLimit);
          this.searchResults = result.results || [];
          this.predictedName = result.predicted_name || "";

          if (this.searchResults.length === 0) {
            alert("Không nhận diện được phim từ video này!");
          }

        } catch (error) {
          console.error("Lỗi upload video:", error);
          alert("Có lỗi xảy ra khi xử lý video!");
          this.clearVideo();
        } finally {
          this.isUploading = false;
        }
      };

      video.onerror = () => {
        alert("Không thể đọc được file video!");
        this.clearVideoInput();
      };

      video.src = URL.createObjectURL(file);
    },

    clearImage() {
      if (this.imageURL) {
        URL.revokeObjectURL(this.imageURL);
      }
      this.imageURL = "";
      this.clearImageInput();
    },

    clearVideo() {
      if (this.videoURL) {
        URL.revokeObjectURL(this.videoURL);
      }
      this.videoURL = "";
      this.clearVideoInput();
    },

    clearAudio() {
      if (this.audioURL) {
        URL.revokeObjectURL(this.audioURL);
      }
      this.audioURL = "";
      this.audioName = "";
      this.clearAudioInput();
    },

    clearImageInput() {
      if (this.$refs.imageInput) {
        this.$refs.imageInput.value = "";
      }
    },

    clearVideoInput() {
      if (this.$refs.videoInput) {
        this.$refs.videoInput.value = "";
      }
    },

    clearAudioInput() {
      if (this.$refs.audioInput) {
        this.$refs.audioInput.value = "";
      }
    }
  },

  beforeUnmount() {
    this.clearImage();
    this.clearVideo();
    this.clearAudioInput();
    this.clearAudio();
  },
};
</script>

<style scoped>
.container {
  max-width: 900px;
}

.form-label {
  font-weight: 500;
  margin-bottom: 0.5rem;
}

video, img {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
