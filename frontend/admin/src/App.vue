<script>
import AppHeader from "@/components/common/AppHeader.vue";

export default {
  components: {
    AppHeader,
  },
  created() {
    this.$router.push('/');
  },
};
</script>


<template class="container">
  <div id="app">
    <div class="container mt-3">
      <router-view />
    </div>
  </div>
</template>

<style>
.page {
  max-width: 400px;
  margin: auto;
}
</style>