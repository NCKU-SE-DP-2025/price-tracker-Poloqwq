<template>
    <div class="register-page">
        <h1>使用者註冊</h1>
        <div class="container">
            <form @submit.prevent="register">
                <input v-model="username" type="text" placeholder="Username" required>
                <p v-if="errors.username" class="error">{{ errors.username }}</p>

                <input v-model="password" type="password" placeholder="Password" required>
                <p v-if="errors.password" class="error">{{ errors.password }}</p>

                <input v-model="passwordConfirm" type="password" placeholder="Password confirm" required>
                <p v-if="errors.passwordConfirm" class="error">{{ errors.passwordConfirm }}</p>

                <div class="ops">
                    <button type="submit" id="register">註冊</button>
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
            password: '',
            passwordConfirm: '',
            errors: {
                username: '',
                password: '',
                passwordConfirm: ''
            }
        };
    },
    methods: {
        register() {
            if (this.validate()) {
                const userStore = useAuthStore();
                userStore.register(this.username, this.password);
            }
        },
        validate() {
            let valid = true;
            this.errors = { username: '', password: '', passwordConfirm: '' };

            if (!this.username.trim()) {
                this.errors.username = 'Username is required.';
                valid = false;
            }
            if (!this.password) {
                this.errors.password = 'Password is required.';
                valid = false;
            }
            if (this.password !== this.passwordConfirm) {
                this.errors.passwordConfirm = 'Passwords do not match!';
                valid = false;
            }
            return valid;
        }
    }
}
</script>

<style scoped>
.register-page {
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
    display: inline-block;
    background-color: #5bc0de;
    color: #fff;
}

#register:hover{
    background-color: #46b8da;
}
</style>