<template>
  <div class="container my-4">
    <div class="card shadow-sm">
      <div class="card-body">
        <h5 class="card-title mb-4">Comments</h5>

        <!-- Danh sách comment -->
        <div
          v-for="comment in comments"
          :key="comment._id"
          class="py-2 border-bottom d-flex justify-content-between align-items-start"
        >
          <div>
            <strong class="text-primary">{{ comment.name }}</strong>
            <div class="ms-2 mt-1">{{ comment.comment }}</div>
          </div>

          <!-- Nút xóa nếu là comment của người dùng hiện tại -->
          <button
            v-if="authStore.user?.id === comment.user_id"
            class="btn btn-sm btn-link text-danger text-decoration-none p-0 ms-2"
            @click="deleteComment(comment._id)"
            title="Xóa comment"
            style="font-size: 2rem;"
          >
            &times;
          </button>
        </div>

        <!-- Thêm comment mới -->
        <form @submit.prevent="submitComment" class="d-flex gap-2 pt-3 border-top mt-3">
          <input
            v-model="newComment"
            type="text"
            placeholder="Write a comment..."
            class="form-control"
          />
          <button type="submit" class="btn btn-primary">
            Send
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import CommentService from '@/services/comment.service';
import UserService from '@/services/user.service';

const route = useRoute();
const authStore = useAuthStore();
const movieId = route.params.movieId;

const comments = ref([]);
const newComment = ref('');

// Cache user name để tránh gọi lại nhiều lần nếu trùng user_id
const userNameCache = {};

const fetchComments = async () => {
  try {
    const res = await CommentService.getByMovieId(movieId);
    const rawComments = res.data;

    const enrichedComments = await Promise.all(
      rawComments.map(async (comment) => {
        let name = 'Unknown';

        // Check cache
        if (userNameCache[comment.user_id]) {
          name = userNameCache[comment.user_id];
        } else {
          const userRes = await UserService.getUserById(comment.user_id);
          if (userRes.status === 'success') {
            name = userRes.user.name;
            userNameCache[comment.user_id] = name; // cache lại
          }
        }

        return {
          ...comment,
          name
        };
      })
    );

    comments.value = enrichedComments;
  } catch (error) {
    console.error("Failed to fetch comments:", error);
  }
};

const submitComment = async () => {
  if (!newComment.value.trim()) return;

  const data = {
    user_id: authStore.user?.id,
    movie_id: movieId,
    comment: newComment.value
  };

  try {
    const res = await CommentService.create(data);

    // Lấy tên user từ cache hoặc từ API
    let userName = userNameCache[authStore.user?.id];
    if (!userName) {
      const userRes = await UserService.getUserById(authStore.user?.id);
      userName = userRes.status === 'success' ? userRes.user.name : 'Unknown';
      userNameCache[authStore.user?.id] = userName;
    }

    const newCommentData = {
      ...res.data,
      name: userName
    };

    comments.value.push(newCommentData);
    newComment.value = '';
  } catch (error) {
    console.error("Failed to post comment:", error);
  }
};

const deleteComment = async (comment_id) => {
  if (!confirm("Bạn có chắc muốn xóa comment này không?")) return;

  try {
    await CommentService.delete(comment_id);
    // Loại bỏ comment khỏi danh sách UI
    comments.value = comments.value.filter(c => c._id !== comment_id);
  } catch (error) {
    console.error("Failed to delete comment:", error);
  }
};

onMounted(() => {
  fetchComments();
});
</script>
