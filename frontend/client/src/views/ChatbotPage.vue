<template>
    <div class="d-flex flex-column min-vh-100">
      <AppHeader />
  
      <div class="flex-grow-1 d-flex">
        <!-- Sidebar -->
        <div
          class="sidebar border-end bg-light position-relative"
          :class="{ collapsed: !showSidebar }"
          style="width: 280px; transition: all 0.3s ease;"
        >
          <div class="p-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h6 class="mb-0">Lịch sử chat</h6>
              <button 
                class="btn btn-sm btn-outline-secondary" 
                @click="toggleSidebar"
                :title="showSidebar ? 'Thu gọn' : 'Mở rộng'"
              >
                <i :class="showSidebar ? 'bi bi-chevron-left' : 'bi bi-chevron-right'"></i>
              </button>
            </div>
            
            <template v-if="showSidebar">
              <button 
                class="btn btn-sm btn-success w-100 mb-3" 
                @click="createNewChat"
              >
                <i class="bi bi-plus-circle me-1"></i>
                Tạo chat mới
              </button>
              
              <div class="chat-history" style="max-height: 60vh; overflow-y: auto;">
                <div
                  v-for="(session, index) in chatHistory"
                  :key="session._id || index"
                  class="chat-item p-2 mb-2 rounded"
                  :class="{ 'active': currentSession && currentSession._id === session._id }"
                  @click="loadChat(session)"
                  style="cursor: pointer; border: 1px solid #dee2e6;"
                >
                  <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                      <small class="text-muted">{{ formatDate(session.createdAt) }}</small>
                      <div class="fw-bold small">{{ session.title || `Chat ${index + 1}` }}</div>
                    </div>
                    <button 
                      class="btn btn-sm btn-outline-danger"
                      @click.stop="deleteChat(session._id)"
                      v-if="session._id"
                    >
                      <i class="bi bi-trash3"></i>
                    </button>
                  </div>
                </div>
                
                <div v-if="chatHistory.length === 0" class="text-center text-muted py-3">
                  <i class="bi bi-chat-dots fs-3"></i>
                  <div>Chưa có lịch sử chat</div>
                </div>
              </div>
            </template>
          </div>
        </div>
  
        <!-- Main Chat Area -->
        <main class="flex-grow-1 d-flex flex-column">
          <div v-if="!authStore.isLoggedIn" class="alert alert-warning text-center m-3">
            <i class="bi bi-exclamation-triangle me-2"></i>
            Bạn cần đăng nhập để sử dụng chatbot.
          </div>
  
          <div v-else class="d-flex flex-column h-100">
            <!-- Chat Header -->
            <div class="border-bottom bg-white p-3">
              <div class="d-flex align-items-center">
                <button 
                  class="btn btn-sm btn-outline-secondary me-3 d-md-none"
                  @click="toggleSidebar"
                >
                  <i class="bi bi-list"></i>
                </button>
                <div>
                  <h6 class="mb-0">
                    <i class="bi bi-robot me-2"></i>
                    {{ currentSession?.title || 'Chat với AI Bot' }}
                  </h6>
                  <small class="text-muted">Trợ lý AI thông minh</small>
                </div>
              </div>
            </div>
  
            <!-- Chat Messages -->
            <div 
              ref="chatContainer"
              class="flex-grow-1 p-3"
              style="overflow-y: auto; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);"
            >
              <div v-if="messages.length === 0" class="text-center text-muted py-5">
                <i class="bi bi-chat-heart fs-1"></i>
                <h5 class="mt-3">Chào mừng bạn!</h5>
                <p>Hãy bắt đầu cuộc trò chuyện với AI Bot</p>
              </div>
  
              <div v-for="(msg, index) in messages" :key="index" class="mb-3">
                <div 
                  class="d-flex"
                  :class="msg.sender === 'user' ? 'justify-content-end' : 'justify-content-start'"
                >
                  <div 
                    class="message-bubble p-3 rounded-3 shadow-sm"
                    :class="msg.sender === 'user' ? 'bg-primary text-white' : 'bg-white'"
                    style="max-width: 70%;"
                  >
                    <div class="d-flex align-items-center mb-1">
                      <i :class="msg.sender === 'user' ? 'bi bi-person-fill' : 'bi bi-robot'" class="me-2"></i>
                      <small class="fw-bold">{{ msg.sender === 'user' ? 'Bạn' : 'AI Bot' }}</small>
                    </div>
                    <div class="message-text">{{ msg.text }}</div>
                    <small class="opacity-75 mt-1 d-block">{{ formatTime(msg.timestamp) }}</small>
                  </div>
                </div>
              </div>
  
              <!-- Typing indicator -->
              <div v-if="isTyping" class="d-flex justify-content-start mb-3">
                <div class="bg-white p-3 rounded-3 shadow-sm">
                  <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
  
            <!-- Input Form -->
            <div class="border-top bg-white p-3">
              <form @submit.prevent="sendMessage" class="d-flex gap-2">
                <input
                  ref="messageInput"
                  v-model="userInput"
                  type="text"
                  class="form-control"
                  placeholder="Nhập tin nhắn của bạn..."
                  :disabled="isTyping"
                  required
                />
              </form>
            </div>
          </div>
        </main>
      </div>
  
      <AppFooter />
    </div>
  </template>
  
  <script>
  import { ref, onMounted, nextTick, computed } from 'vue';
  import { useRouter } from 'vue-router';
  import { useAuthStore } from '@/store/auth';
  import {useChatbotStore} from '@/store/chatbot'
  import AppHeader from '@/components/common/AppHeader.vue';
  import AppFooter from '@/components/common/AppFooter.vue';
  import chatbotService from '@/services/chatbot.service';
  
  export default {
    name: 'ChatPage',
    components: {
      AppHeader,
      AppFooter
    },
    setup() {
      const authStore = useAuthStore();
      const chatbotStore = useChatbotStore();
      const router = useRouter();
  
      const showSidebar = ref(true);
      const toggleSidebar = () => (showSidebar.value = !showSidebar.value);
  
      const userId = ref(null);
      const userInput = ref('');
      const messages = ref([]);
      const chatHistory = ref([]);
      const currentSession = ref(null);
      const isTyping = ref(false);
      const chatContainer = ref(null);
      const messageInput = ref(null);
  
      // Computed properties
      const currentUserId = computed(() => {
        return authStore.user?.id || authStore.user?._id;
      });
  
      // Utility functions
      const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric'
        });
      };
  
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
  
      // Chat functions
      const createNewChat = () => {
        messages.value = [];
        currentSession.value = null;
        chatbotStore.clearChatId();
        nextTick(() => {
          messageInput.value?.focus();
        });
      };
  
      const sendMessage = async () => {
        const text = userInput.value.trim();
        if (!text || isTyping.value) return;
  
        const userMessage = {
          sender: 'user',
          text,
          timestamp: new Date()
        };
  
        messages.value.push(userMessage);
        userInput.value = '';
        isTyping.value = true;
        scrollToBottom();
  
        try {
          // Sử dụng chat ID từ store hoặc current session
          const chatId = chatbotStore.currentChatId || currentSession.value?._id;
          const res = await chatbotService.sendMessage(currentUserId.value, text, chatId);
  
          const botMessage = {
            sender: 'bot',
            text: res.answer || 'Xin lỗi, tôi không thể trả lời lúc này.',
            timestamp: new Date()
          };
  
          messages.value.push(botMessage);
  
          // Xử lý session management
          if (!currentSession.value && res.hischat_id) {
            // Tạo session mới
            const newSession = {
              _id: res.hischat_id,
              title: text.length > 30 ? text.substring(0, 30) + '...' : text,
              messages: [...messages.value],
              createdAt: new Date()
            };
  
            currentSession.value = newSession;
            chatHistory.value.unshift(newSession);
            chatbotStore.setChatId(res.hischat_id);
            
          } else if (currentSession.value || chatbotStore.currentChatId) {
            // Cập nhật session hiện tại
            const updateId = currentSession.value?._id || chatbotStore.currentChatId;
            
            if (updateId) {
              try {
                await chatbotService.updateHistory(updateId, text);
                
                if (currentSession.value) {
                  currentSession.value.messages = [...messages.value];
                  
                  // Cập nhật trong danh sách lịch sử
                  const sessionIndex = chatHistory.value.findIndex(s => s._id === currentSession.value._id);
                  if (sessionIndex !== -1) {
                    chatHistory.value[sessionIndex] = { ...currentSession.value };
                  }
                }
              } catch (updateError) {
                console.warn('Failed to update history:', updateError);
              }
            }
          }
  
        } catch (error) {
          console.error('Error sending message:', error);
          const errorMessage = {
            sender: 'bot',
            text: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.',
            timestamp: new Date()
          };
          messages.value.push(errorMessage);
        } finally {
          isTyping.value = false;
          scrollToBottom();
          nextTick(() => {
            messageInput.value?.focus();
          });
        }
      };
  
      const fetchChatHistory = async () => {
        try {
          const data = await chatbotService.getHistory(currentUserId.value);
          console.log(data)
          chatHistory.value = Array.isArray(data) ? data : [];
        } catch (error) {
          console.error('Error fetching chat history:', error);
          chatHistory.value = [];
        }
      };
  
      const loadChat = async (session) => {
        if (currentSession.value?._id === session._id) return;
  
        currentSession.value = session;
        messages.value = session.messages || [];
        chatbotStore.setChatId(session._id);
        scrollToBottom();
        
        nextTick(() => {
          messageInput.value?.focus();
        });
      };
  
      const deleteChat = async (chatId) => {
        if (!chatId) return;
        
        if (!confirm('Bạn có chắc chắn muốn xóa cuộc trò chuyện này?')) return;
  
        try {
          await chatbotService.deleteHistoryById(chatId);
          
          // Remove from history list
          chatHistory.value = chatHistory.value.filter(chat => chat._id !== chatId);
          
          // If deleted chat is current, create new
          if (currentSession.value?._id === chatId || chatbotStore.currentChatId === chatId) {
            createNewChat();
          }
          
        } catch (error) {
          console.error('Error deleting chat:', error);
          alert('Có lỗi khi xóa cuộc trò chuyện');
        }
      };
  
      // Lifecycle
      onMounted(() => {
        if (!authStore.isLoggedIn) {
          setTimeout(() => router.push('/login'), 1500);
          return;
        }
  
        userId.value = currentUserId.value;
        fetchChatHistory();
        
        // Khôi phục session nếu có chat ID trong store
        if (chatbotStore.currentChatId) {
          const existingSession = chatHistory.value.find(s => s._id === chatbotStore.currentChatId);
          if (existingSession) {
            loadChat(existingSession);
          }
        }
        
        nextTick(() => {
          messageInput.value?.focus();
        });
      });
  
      return {
        authStore,
        showSidebar,
        toggleSidebar,
        userInput,
        messages,
        chatHistory,
        currentSession,
        isTyping,
        chatContainer,
        messageInput,
        sendMessage,
        loadChat,
        createNewChat,
        deleteChat,
        formatDate,
        formatTime
      };
    }
  };
  </script>
  
  <style scoped>
  .sidebar.collapsed {
    width: 60px !important;
  }
  
  .chat-item:hover {
    background-color: #f8f9fa !important;
  }
  
  .chat-item.active {
    background-color: #e3f2fd !important;
    border-color: #2196f3 !important;
  }
  
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
    align-items: center;
    gap: 4px;
  }
  
  .typing-indicator span {
    height: 8px;
    width: 8px;
    background-color: #999;
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
    0%, 80%, 100% {
      transform: scale(0.8);
      opacity: 0.5;
    }
    40% {
      transform: scale(1);
      opacity: 1;
    }
  }
  
  @media (max-width: 768px) {
    .sidebar {
      position: absolute;
      z-index: 1000;
      height: 100%;
    }
    
    .sidebar.collapsed {
      transform: translateX(-100%);
      width: 280px !important;
    }
  }
  </style>