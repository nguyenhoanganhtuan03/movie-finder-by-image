<template>
  <div class="chat-widget position-fixed bottom-0 end-0 m-4 shadow-lg rounded-4 overflow-hidden"
    style="width: 350px; max-height: 80vh; z-index: 9999;">
    <!-- Header -->
    <div class="bg-primary text-white p-3 d-flex justify-content-between align-items-center">
      <div>
        <i class="bi bi-robot me-2"></i> AI ChatBot
      </div>
      <button class="btn btn-sm btn-light" @click="handleClose">
        <i class="bi bi-x"></i>
      </button>
    </div>

    <!-- Nội dung chat -->
    <div class="bg-light d-flex flex-column h-100" style="height: calc(100% - 56px);">
      <div ref="chatContainer" class="flex-grow-1 p-3 overflow-auto"
        style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);">
        <div v-if="messages.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-chat-heart fs-1"></i>
          <h5 class="mt-3">Chào bạn!</h5>
          <p>Bắt đầu trò chuyện với AI nhé.</p>
        </div>

        <div v-for="(msg, index) in messages" :key="index" class="mb-3">
          <div :class="msg.sender === 'user' ? 'text-end' : 'text-start'">
            <div class="message-bubble p-2 rounded-3 d-inline-block"
              :class="msg.sender === 'user' ? 'bg-primary text-white' : 'bg-white'" style="max-width: 75%;">
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

      <!-- Input -->
      <form @submit.prevent="sendMessage" class="p-2 border-top bg-white d-flex gap-2">
        <input ref="messageInput" v-model="userInput" type="text" class="form-control" placeholder="Nhập tin nhắn..."
          :disabled="isTyping" required />
      </form>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue';
import chatbotService from '@/services/chatbot.service';
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
    const chatStarted = ref(false);

    const chatId = ref(chatbotStore.currentChatId);

    const formatTime = (timestamp) => {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      return date.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    const scrollToBottom = () => {
      nextTick(() => {
        if (chatContainer.value) {
          chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }
      });
    };

    const loadChatHistory = async (id) => {
      try {
        const res = await chatbotService.getChatById(id);
        console.log(res)
        const contentArr = res.content || [];

        const formattedMessages = contentArr.flatMap(item => {
          const messages = [];
          if (item.user) {
            messages.push({ sender: 'user', text: item.user, timestamp: new Date() });
          }
          if (item.bot) {
            messages.push({ sender: 'bot', text: item.bot, timestamp: new Date() });
          }
          return messages;
        });

        messages.value = formattedMessages;
        chatStarted.value = true;
        scrollToBottom();
      } catch (err) {
        console.error("❌ Không thể tải lịch sử chat:", err);
        messages.value.push({
          sender: 'bot',
          text: 'Không thể tải lịch sử chat.',
          timestamp: new Date()
        });
      }
    };

    const sendMessage = async () => {
      const text = userInput.value.trim();
      if (!text || isTyping.value) return;

      const userId = authStore.user?.id;
      if (!userId) {
        messages.value.push({
          sender: 'bot',
          text: 'Không xác định được người dùng. Vui lòng đăng nhập.',
          timestamp: new Date()
        });
        return;
      }

      messages.value.push({ sender: 'user', text, timestamp: new Date() });
      userInput.value = '';
      isTyping.value = true;
      scrollToBottom();

      try {
        let res;

        if (!chatId.value) {
          // ✅ Chưa có cuộc trò chuyện nào, tạo mới
          res = await chatbotService.sendMessage(userId, text);
          if (res.hischat_id) {
            chatbotStore.setChatId(res.hischat_id);
            chatId.value = res.hischat_id; // ✅ cập nhật reactive chatId
          }
          chatStarted.value = true;
        } else {
          // ✅ Đã có session, tiếp tục gửi tin nhắn
          res = await chatbotService.updateHistory(chatId.value, text);
          chatStarted.value = true;
        }

        // ✅ Lấy câu trả lời bot mới nhất từ updated_history.content
        let botAnswer = res.answer || 'Xin lỗi, tôi chưa thể trả lời.';
        if (res.updated_history && Array.isArray(res.updated_history.content)) {
          const contentArr = res.updated_history.content;
          const lastItem = contentArr[contentArr.length - 1];
          if (lastItem && lastItem.bot) {
            botAnswer = lastItem.bot;
          }
        }

        messages.value.push({
          sender: 'bot',
          text: botAnswer,
          timestamp: new Date()
        });

      } catch (e) {
        console.error('Chatbot error:', e);
        messages.value.push({
          sender: 'bot',
          text: 'Đã xảy ra lỗi. Vui lòng thử lại.',
          timestamp: new Date()
        });
      } finally {
        isTyping.value = false;
        scrollToBottom();
        nextTick(() => messageInput.value?.focus());
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

    const handleClose = () => {
      emit('close');
    };

    onMounted(async () => {
      if (chatId.value) {
        await loadChatHistory(chatId.value);
      }
    });

    return {
      messages,
      userInput,
      isTyping,
      chatContainer,
      messageInput,
      sendMessage,
      formatTime,
      handleClose,
      loadChatHistory
    };
  }
};
</script>


<style scoped>
.chat-widget {
  background-color: #fff;
  display: flex;
  flex-direction: column;
  border: 1px solid #ccc;
  width: 350px;
  height: 80vh;
  max-height: 80vh;
}

/* Cố định header */
.chat-widget>div:first-child {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: #0d6efd;
  /* giữ màu bg-primary */
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ccc;
}

/* Container chính phần chat + input */
.chat-widget>div:nth-child(2) {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  min-height: 0;
}

/* Container chứa tin nhắn */
.flex-grow-1.p-3.overflow-auto {
  flex-grow: 1;
  overflow-y: auto;
  min-height: 0;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 1rem;
}

/* Input chat luôn cố định ở dưới */
form.p-2.border-top.bg-white.d-flex.gap-2 {
  flex-shrink: 0;
  /* ✅ ngăn không cho bị co/ẩn */
  position: sticky;
  bottom: 0;
  background-color: #fff;
  z-index: 5;
  border-top: 1px solid #ddd;
}

/* Các tin nhắn và phần input giữ nguyên */
.message-bubble {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
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

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {

  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }

  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
