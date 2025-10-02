<script setup>
// import { RouterView } from 'vue-router';
import NavBar from './components/NavBar.vue'

  
</script>
<template>
  <NavBar class="navbar"></NavBar>
  <RouterView class="render"></RouterView>
</template>


<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
.navbar{
  z-index: 1000;
  position: fixed;
  top: 0;
}
.render{
  margin-top: 4.5em;
}
</style>
