<template>
    <div class="user-page">
      <AppHeader />
  
      <main class="main-container">
        <UserDetail />
      </main>
  
      <AppFooter />
    </div>
  </template>
  
  <script>
  import AppHeader from "@/components/common/AppHeader.vue";
  import AppFooter from "@/components/common/AppFooter.vue";
  import UserDetail from "@/components/users/userDetail.vue";
  
  export default {
    name: "UserPage",
    components: {
      AppHeader,
      AppFooter,
      UserDetail,
    },
  };
  </script>
  
  <style scoped>
  .main-container {
    min-height: calc(100vh - 160px); /* trừ header + footer */
    padding: 40px 20px;
    background-color: #f5f5f5;
  }
  </style>
  