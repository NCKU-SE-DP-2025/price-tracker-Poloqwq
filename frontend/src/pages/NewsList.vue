<template>
    <div class="wrapper">
        <h1>相關新聞</h1>
        <div class="search-bar">
            <input v-model="prompt" placeholder="輸入你的搜尋prompt，讓AI幫你找相關的新聞吧！例如：「我想獲取雞蛋價格的資訊」" class="search-input"/>
            <i class="bi bi-search" @click="searchNewsBasedOnPrompt"></i>
        </div>
        <div class="content">
            <div v-if="isLoading">loading...</div>
            <div v-else>
                <NewsItem v-for="(news, index) in newsList" :key="news.id" :news="news" 
                    @show-dialog="showDialog(news)" @fetch-summary="fetchSummary(news.content, index)"/>
                <div v-if="isEmpty">
                    <p>找不到相關新聞！</p>
                </div>
            </div>
        </div>
        <NewsDialog :news="selectedNews" v-model:visible="isDialogVisible" />
    </div>
</template>

<script>
import { useNewsStore } from '@/stores/news';
import { onMounted } from 'vue';
import NewsItem from '@/components/NewsItem.vue';
import NewsDialog from '@/components/NewsDialog.vue';

export default {
    components: {
        NewsItem,
        NewsDialog
    },
    data() {
        return {
            prompt: '',
            newsStore: useNewsStore(),
            selectedNews: null,
            isDialogVisible: false
        };
    },
    created() {
        onMounted(() => {
            this.newsStore.fetchNews();
        });
    },
    computed: {
        newsList() {
            return this.newsStore.getNews;
        },
        isLoading() {
            return this.newsStore.isLoading;
        },
        isEmpty() {
            return this.newsStore.newsList.length === 0;
        }
    },
    methods: {
        searchNewsBasedOnPrompt() {
            if (this.prompt.trim()) {
                this.newsStore.promptSearchNews(this.prompt);
                this.prompt = '';
            }
        },
        showDialog(news) {
            this.selectedNews = news;
            this.isDialogVisible = true;
        },
        fetchSummary(content, index){
            this.newsStore.fetchNewsSummary(content, index);
        }
    }
};
</script>

<style scoped>
.wrapper {
    padding: 3em 5em;
    background: #f3f3f3;
    min-height: calc(100vh - 4.5em);
    height: calc(100% - 4.5em);
    box-sizing: border-box;
    width: 100%;
}
.content {
    background-color: white;
    margin-top: 1em;
    border-radius: 1em;
    padding: 1em 3em;
}
.news-item{
    border-bottom: #aaaaaa 1px solid;
}
.news-item:last-child{
    border-bottom: none;
}
.search-bar{
    background-color: white;
    display: inline-flex;
    border-radius: .5em;
    box-sizing: border-box;
    text-align: start;
    margin-top: 1em;
    padding: 1em;
    width: 80%;
}

.search-bar input{
    border: none;
    outline: none;
    font-size: .9em;
    box-sizing: border-box;
    flex-grow: 1;
    margin-right: 1em;
}

.search-bar i{
    cursor: pointer;
}

.search-bar button:hover{
    cursor: pointer;
}
</style>