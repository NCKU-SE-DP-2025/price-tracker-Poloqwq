<script setup>
import { useAuthStore } from '@/stores/auth';
import { computed, ref, onMounted, onBeforeUnmount } from 'vue';


    const name = ref('NavBar');
    const userStore = useAuthStore();
    const isMobile = ref(window.matchMedia("(max-width: 768px)").matches);
    const isMenuOpen = ref(false);

    let mq;
    function checkMobile(match){
        isMobile.value = match.matches;
        if(!isMobile.value)  isMenuOpen.value = true;
        else isMenuOpen.value = false;
    }

    onMounted(() => {
        isMenuOpen.value = !isMobile.value ? true : false;
        mq = window.matchMedia("(max-width: 768px)");
        mq.addEventListener('change', checkMobile);
        checkMobile(mq);
    });

    onBeforeUnmount(() => {
        mq.removeEventListener('change', checkMobile);
    });
    
    const isLoggedIn = computed(() => {
        return userStore.isLoggedIn;
    })
    const getUserName = computed(() => {
        return userStore.getUserName;
    })

    
    function logout(){
        userStore.logout();
    }
    
    function toggleMenu(){
        if(isMobile.value) isMenuOpen.value = !isMenuOpen.value;
    }

</script>
<template>
    <nav class="navbar">
        <div class="title"> 
            <RouterLink to="/overview" style="display: flexbox;">價格追蹤小幫手</RouterLink>
            <img @click="toggleMenu" src="@/assets/hamburger.jpg" style="display: flexbox;">
        </div>
        <ul class="options" v-if="isMenuOpen">
            <li><RouterLink to="/overview">物價概覽</RouterLink></li>
            <li><RouterLink to="/trending">物價趨勢</RouterLink></li>
            <li><RouterLink to="/news">相關新聞</RouterLink></li>
            <li v-if="!isLoggedIn"><RouterLink to="/login">登入</RouterLink></li>
            <li v-else @click="logout">Hi, {{getUserName}}! 登出</li>
        </ul>
    </nav>
</template>


<style scoped>

@media screen and (min-width: 768px) {
    
    .navbar {
        display: flex;
        justify-content: space-between;
        background-color: #f3f3f3;
        padding: 1.5em;
        height: 4.5em;
        width: 100%;
        align-items: center;
        box-shadow: 0 0 5px #000000;
    }
    
    .navbar ul {
        list-style: none;
        display: flex;
        justify-content: space-around;
    }
    
    .title > a{
        font-weight: bold;
        color: #2c3e50 !important;
    }
    .title > img{
        width: 0px;
        height: 0px;
    }
    
    .navbar li {
        color: #575B5D;
        margin: 0 .5em;
        font-size: 1.2em;
    }
    
    
}


@media screen and (max-width: 768px) {
    .navbar {
        width: 100%;
        flex-direction: column;
        height: auto;
        padding: 1em;
        padding-bottom: 0px;
        background-color: #f3f3f3;
        align-items: center;
        box-shadow: 0 0 5px #000000;
    }
    .navbar ul {
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        list-style: none;
        justify-content: space-around;
    }
    .navbar li {
        width: 100%;
        text-align: center;
        height: fit-content;
        padding: 10px;
        border-top: 1px solid #D5D5D5;
        color: #575B5D;
        margin: 0 .5em;
        font-size: 1.2em;
    }
    
    .title {
        width:100%;
        justify-content: space-between;
    }
    .title > img{
        width: 30px;
        height: 30px;
        
    }
}


.title {
    font-size: 1.4em;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.navbar a {
    text-decoration: none;
    color: #575B5D;
}
.navbar li:hover{
    cursor: pointer;
    font-weight: bold;
}

</style>