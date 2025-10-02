<template>
    <div v-if="visible" class="cover">
        <div class="news-dialog">
            <i class="bi bi-x-lg close-btn" @click="close"></i>
            <div class="content">
                <h2>{{ news.title }}</h2>
                <p class="time">{{ news.time }}</p>
                <p>原文連結：<a :href="news.url" target="_blank">{{news.url}}</a></p>
                <p v-for="paragraph, index in formattedContent" :key="index">{{ paragraph }}</p>
            </div>

        </div>
    </div>
</template>

<script>
export default {
    props: {
        news: {
            type: Object,
            required: true
        },
        visible: {
            type: Boolean,
            default: false
        }
    },
    methods: {
        close() {
            this.$emit('update:visible', false);
        }
    },
    computed:{
        formattedContent() {
            if(!this.news.content) return '';
            return this.news.content.split('\r\n');
        }
    }
};
</script>

<style scoped>
.news-dialog {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 90%;
    height: 90%;
    transform: translate(-50%, -50%);
    background: white;
    padding: 20px;
    border-radius: 8px;
    padding: 3em 4em;
}
.content{
    overflow-y: auto;
    height: 100%;
    text-align: start;
    padding: 3em;
}
.time{
    color: #888;
}
.news-dialog h2{
    margin: 0;
    font-size: 1.5em;
}
.news-dialog p{
    font-size: 1.2em;
    margin: 1em 0;
}
.cover{
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    position: fixed;
    z-index: 1000;
    top: 0;
    left: 0;
    content: ' ';
    background-color: rgba(0, 0, 0, 0.5);
}
.close-btn{
    position: absolute;
    top: .5em;
    right: .5em;
    font-size: 2em;
    cursor: pointer;
    color: #888;
}
</style>