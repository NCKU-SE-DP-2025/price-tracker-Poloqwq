<template>
    <div class="login-page">
        <h1>使用者登入</h1>
        <div class="container">
            <form @submit.prevent="login">
                <input v-model="username" type="text" placeholder="Username" required>
                <input v-model="password" type="password" placeholder="Password" required>
                <p v-if="loginError" class="error">{{ loginError }}</p>
                <div class="ops">
                    <button type="button" id="register"><RouterLink to="/register">註冊</RouterLink></button>
                    <button type="submit" id="login">登入</button>
                </div>
            </form>
        </div>
    </div>
</template>

<script>
import { useAuthStore } from '@/stores/auth';

export default {
    data() {
        return {
            username: '',
            password: ''
        };
    },
    methods: {
        login() {
            const userStore = useAuthStore();
            userStore.login(this.username, this.password);
        }
    },
    computed: {
        loginError(){
            const userStore = useAuthStore();
            return userStore.getLoginError;
        }
    }
}
</script>

<style scoped>
.login-page {
    padding: 3em 5em;
    background: #f3f3f3;
    min-height: calc(100vh - 4.5em);
    height: calc(100% - 4.5em);
    box-sizing: border-box;
}

.error{
    color: red;
}

.container {
    margin-top: 2em;
    background: #fff;
    padding: 2em;
    border-radius: 1em;
    box-shadow: 0 0 10px rgba(0, 0, 0, .1);
}

form{
    display: flex;
    flex-direction: column;
}

form > input{
    margin: .25em 0;
    padding: .5em 1em;
    font-size: 1.2em;
    border: 1px solid #ccc;
    border-radius: .5em;
}

.ops{
    margin-top: .5em;
    display: flex;
    justify-content: center;
}

.ops > button{
    padding: .5em 1em;
    margin: 0 .5em;
    font-size: 1.2em;
    border: none;
    border-radius: .5em;
    cursor: pointer;
}

#register{
    background-color: #F3F3F3;
    border: 1px solid #ccc;
}

#register > a{
    text-decoration: none;
    color: #000;
}

#register:hover{
    background-color: #e8e8e8;
}

#login{
    background-color: #5bc0de;
    color: #fff;
}

#login:hover{
    background-color: #46b8da;
}
</style>