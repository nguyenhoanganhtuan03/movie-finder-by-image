<template>
  <div
    ref="chatWidget"
    class="chat-widget shadow-lg rounded-4"
    :style="widgetStyle"
  >
    <!-- Resize handle -->
    <div class="resize-handle" @mousedown="startResizing" title="Kéo để thay đổi kích thước">
      <i class="bi bi-box-arrow-in-up-left text-white"></i>
    </div>

    <!-- Header -->
    <div class="chat-header">
      <div>
        <i class="bi bi-robot me-2"></i> ChatBot
      </div>
      <div class="d-flex gap-2">
        <button class="btn btn-sm btn-light" @click="resetChat" title="Tạo mới">
          <i class="bi bi-arrow-clockwise"></i>
        </button>
        <button class="btn btn-sm btn-light" @click="handleClose">
          <i class="bi bi-x"></i>
        </button>
      </div>
    </div>

    <!-- Nội dung chat -->
    <div class="chat-body">
      <div class="chat-content" ref="chatContainer">
        <div class="chat-messages p-3">
          <div v-if="messages.length === 0" class="text-center text-muted py-5">
            <i class="bi bi-chat-heart fs-1"></i>
            <h5 class="mt-3">Chào bạn!</h5>
            <p>Bắt đầu trò chuyện với AI nhé.</p>
          </div>

          <div v-for="(msg, index) in messages" :key="index" class="mb-3">
            <div :class="msg.sender === 'user' ? 'text-end' : 'text-start'">
              <div
                class="message-bubble p-2 rounded-3 d-inline-block"
                :class="msg.sender === 'user' ? 'bg-primary text-white' : 'bg-white'"
                style="max-width: 75%;"
              >
                <small class="fw-bold d-block mb-1">
                  <i :class="msg.sender === 'user' ? 'bi bi-person-fill' : 'bi bi-robot'"></i>
                  {{ msg.sender === 'user' ? 'Bạn' : 'AI Bot' }}
                </small>
                <div>{{ msg.text }}</div>
                <small class="opacity-75 d-block mt-1">{{ formatTime(msg.timestamp) }}</small>
              </div>
            </div>
          </div>

          <div v-if="isTyping" class="text-start mb-3">
            <div class="bg-white p-2 rounded-3 d-inline-block">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <form @submit.prevent="sendMessageFromInput" class="chat-input p-2 border-top bg-white d-flex gap-2 align-items-center">
        <input
          ref="messageInput"
          v-model="userInput"
          type="text"
          class="form-control"
          placeholder="Nhập tin nhắn..."
          :disabled="isTyping"
        />

        <!-- Input file ẩn -->
        <input
          ref="fileInput"
          type="file"
          class="d-none"
          @change="handleFileUpload"
          accept=".png,.jpg,.jpeg,.mp4,.wav,.mp3"
        />
        <button
          type="button"
          class="btn btn-light"
          @click="$refs.fileInput.click()"
          :disabled="isTyping"
          title="Tải file (ảnh, video, âm thanh)"
        >
          <i class="bi bi-paperclip"></i>
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, onBeforeUnmount, computed, watch } from 'vue';
import chatbotService from '@/services/chatbot.service';
import movieService from '@/services/movie.service';
import finderService from '@/services/finder.service';
import { useAuthStore } from '@/store/auth';
import { useChatbotStore } from '@/store/chatbot';

export default {
  name: 'MiniChatWidget',
  setup(_, { emit }) {
    const authStore = useAuthStore();
    const chatbotStore = useChatbotStore();

    const messages = ref([]);
    const userInput = ref('');
    const isTyping = ref(false);
    const chatContainer = ref(null);
    const messageInput = ref(null);
    const chatWidget = ref(null);
    const chatStarted = ref(false);
    const chatId = ref(chatbotStore.currentChatId);

    const width = ref(350);
    const height = ref(window.innerHeight * 0.8);

    const widgetStyle = computed(() => ({
      position: 'fixed',
      bottom: '1rem',
      right: '1rem',
      width: width.value + 'px',
      height: height.value + 'px',
      zIndex: 9999,
      backgroundColor: '#fff',
      display: 'flex',
      flexDirection: 'column',
      minWidth: '250px',
      minHeight: '300px',
      maxWidth: '100vw',
      maxHeight: '100vh',
      border: '1px solid #ccc',
      overflow: 'hidden',
    }));

    const formatTime = (timestamp) => {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    };

    const scrollToBottom = () => {
      nextTick(() => {
        if (chatContainer.value) {
          chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }
      });
    };

    watch(messages, () => {
      scrollToBottom();
    }, { deep: true });

    const loadChatHistory = async (id) => {
      try {
        const res = await chatbotService.getChatById(id);
        const contentArr = res.content || [];
        const formattedMessages = contentArr.flatMap(item => {
          const msgs = [];
          if (item.user) msgs.push({ sender: 'user', text: item.user, timestamp: new Date() });
          if (item.bot) msgs.push({ sender: 'bot', text: item.bot, timestamp: new Date() });
          return msgs;
        });
        messages.value = formattedMessages;
        chatStarted.value = true;
        scrollToBottom();
      } catch (err) {
        messages.value.push({ sender: 'bot', text: 'Không thể tải lịch sử chat.', timestamp: new Date() });
      }
    };

    const sendMessage = async (text) => {
      const messageText = (text ?? '').toString().trim();
      if (!messageText || isTyping.value) return;

      const userId = authStore.user?.id;
      if (!userId) {
        messages.value.push({ sender: 'bot', text: 'Vui lòng đăng nhập.', timestamp: new Date() });
        return;
      }

      // hiển thị user message
      messages.value.push({ sender: 'user', text: messageText, timestamp: new Date() });
      isTyping.value = true;
      scrollToBottom();

      try {
        let res;
        if (!chatId.value) {
          res = await chatbotService.sendMessage(userId, messageText);
          if (res.hischat_id) {
            chatbotStore.setChatId(res.hischat_id);
            chatId.value = res.hischat_id;
          }
        } else {
          res = await chatbotService.updateHistory(chatId.value, messageText, userId);
        }

        let botAnswer = res.answer || 'Xin lỗi, tôi chưa thể trả lời.';
        const contentArr = res.updated_history?.content;
        if (Array.isArray(contentArr) && contentArr.at(-1)?.bot) {
          botAnswer = contentArr.at(-1).bot;
        }

        messages.value.push({ sender: 'bot', text: botAnswer, timestamp: new Date() });
      } catch (e) {
        messages.value.push({ sender: 'bot', text: 'Lỗi khi gửi tin.', timestamp: new Date() });
      } finally {
        isTyping.value = false;
        scrollToBottom();
        nextTick(() => messageInput.value?.focus());
      }
    };

    // gửi ngầm, không hiển thị user message
    const sendHiddenMessage = async (text) => {
      const messageText = (text ?? '').toString().trim();
      if (!messageText || isTyping.value) return;

      const userId = authStore.user?.id;
      if (!userId) return;

      isTyping.value = true;
      try {
        let res;
        if (!chatId.value) {
          res = await chatbotService.sendMessage(userId, messageText);
          if (res.hischat_id) {
            chatbotStore.setChatId(res.hischat_id);
            chatId.value = res.hischat_id;
          }
        } else {
          res = await chatbotService.updateHistory(chatId.value, messageText, userId);
        }

        let botAnswer = res.answer || null;
        const contentArr = res.updated_history?.content;
        if (Array.isArray(contentArr) && contentArr.at(-1)?.bot) {
          botAnswer = contentArr.at(-1).bot;
        }

        if (botAnswer) {
          messages.value.push({ sender: 'bot', text: botAnswer, timestamp: new Date() });
        }
      } catch (e) {
        console.error(e);
      } finally {
        isTyping.value = false;
      }
    };

    // Hàm riêng cho input submit
    const sendMessageFromInput = () => {
      const text = (userInput.value ?? '').toString().trim();
      if (!text) return;
      userInput.value = '';
      sendMessage(text);
    };

    const handleFileUpload = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      messages.value.push({
        sender: 'user',
        text: `📎 Bạn đã tải lên: ${file.name}`,
        timestamp: new Date()
      });

      try {
        let result;
        let movieName = null;
        const ext = file.name.split('.').pop().toLowerCase();

        if (['wav', 'mp3'].includes(ext)) {
          result = await finderService.searchByAudio(file, 0.8, 3);
        } else if (['png', 'jpg', 'jpeg', 'mp4'].includes(ext)) {
          result = await movieService.searchByFile(file, 0.8, 3);
        }

        if (result) {
          if (Array.isArray(result.predicted_names) && result.predicted_names.length > 0) {
            movieName = result.predicted_names[0];
          } else if (Array.isArray(result.results) && result.results.length > 0) {
            movieName = result.results[0].name || result.results[0].title;
          }
        }

        if (movieName && movieName !== "Khác") {
          const autoPrompt = `Tôi vừa tải lên một ${['wav','mp3'].includes(ext) ? 'đoạn âm thanh' : (ext==='mp4' ? 'video' : 'ảnh')} và hệ thống nhận dạng được phim: "${movieName}". Hãy cho tôi biết thêm thông tin về bộ phim này.`;

          await sendHiddenMessage(autoPrompt);
        } else {
          messages.value.push({
            sender: 'bot',
            text: '❌ Không tìm thấy phim phù hợp từ file đã tải lên.',
            timestamp: new Date()
          });
        }

      } catch (err) {
        console.error(err);
        messages.value.push({
          sender: 'bot',
          text: '⚠️ Lỗi khi xử lý file tải lên.',
          timestamp: new Date()
        });
      } finally {
        e.target.value = '';
      }
    };

    const resetChat = () => {
      messages.value = [];
      userInput.value = '';
      chatbotStore.clearChatId();
      chatId.value = null;
      chatStarted.value = false;
      nextTick(() => messageInput.value?.focus());
    };

    const handleClose = () => emit('close');

    // Resize handle logic
    let isResizing = false;
    let startX = 0, startY = 0, startWidth = 0, startHeight = 0;

    const startResizing = (e) => {
      isResizing = true;
      startX = e.clientX;
      startY = e.clientY;
      startWidth = width.value;
      startHeight = height.value;
      document.addEventListener('mousemove', doResize);
      document.addEventListener('mouseup', stopResizing);
    };

    const doResize = (e) => {
      if (!isResizing) return;
      const dx = startX - e.clientX;
      const dy = startY - e.clientY;
      width.value = Math.min(Math.max(startWidth + dx, 250), window.innerWidth);
      height.value = Math.min(Math.max(startHeight + dy, 300), window.innerHeight);
    };

    const stopResizing = () => {
      isResizing = false;
      document.removeEventListener('mousemove', doResize);
      document.removeEventListener('mouseup', stopResizing);
    };

    onBeforeUnmount(() => stopResizing());
    onMounted(() => { if (chatId.value) loadChatHistory(chatId.value); });

    return {
      messages,
      userInput,
      isTyping,
      chatContainer,
      messageInput,
      sendMessage,
      sendHiddenMessage,
      sendMessageFromInput,
      formatTime,
      handleClose,
      loadChatHistory,
      resetChat,
      chatWidget,
      startResizing,
      widgetStyle,
      handleFileUpload
    };
  }
};
</script>



<style scoped>
.chat-widget {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  min-width: 250px;
  min-height: 300px;
  max-width: 100vw;
  max-height: 100vh;
  border: 1px solid #ccc;
  overflow: hidden;
  z-index: 9999;
}
.chat-header {
  background-color: #0d6efd;
  color: white;
  padding: 1rem;
  padding-left: 25px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ccc;
}
.chat-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  position: relative;
  overflow: hidden;
}
.chat-content {
  flex: 1;
  overflow-y: auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}
.chat-messages {
  display: flex;
  flex-direction: column;
}
.chat-input {
  background: white;
  z-index: 9;
  flex-shrink: 0;
}
.resize-handle {
  position: absolute;
  top: 3px;
  left: 5px;
  width: 20px;
  height: 20px;
  background: none;
  opacity: 0.5;
  cursor: nwse-resize;
  z-index: 9999;
  border-bottom-right-radius: 4px;
}
.message-bubble {
  animation: fadeInUp 0.3s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
}
.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
