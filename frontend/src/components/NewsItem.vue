<template>
    <div class="news-item">
        <div class="container" >
            <div class="texts" @click="showDialog">
                <h2>{{ news.title }}</h2>
                <p class="time">{{ news.time }}</p>
                <div v-if="hasDetails">
                    <p><strong>原因：</strong> {{ news.reason }}</p>
                    <p><strong>影響：</strong> {{ news.summary }}</p>
                </div>
                <div v-else>
                    <p>{{ shortContent }}</p>
                </div>
            </div>
            <i v-if="!hasDetails && !news.isSummaryLoading && isLoggedIn" class="bi bi-stars summary-btn" @click="fetchSummary"></i>
            <div v-if="!hasDetails && news.isSummaryLoading && isLoggedIn" class="loader"></div>
        </div>
        <div class="upvote-btn" @click="toggleUpvote(news.id)" v-if="'upvotes' in news">
            <i class="bi bi-fire" :class="{'fire-upvoted': news.is_upvoted}"></i>
            <span>{{ news.upvotes }}</span>
        </div>

    </div>
</template>

<script>
import { useAuthStore } from '@/stores/auth';
import { useNewsStore } from '@/stores/news';
export default {
    props: {
        news: {
            type: Object,
            required: true
        }
    },
    computed: {
        hasDetails() {
            return this.news.reason && this.news.summary;
        },
        shortContent() {
            return this.news.content.length > 200 ? this.news.content.substr(0, 200) + '...' : this.news.content;
        },
        isLoggedIn(){
            const userStore = useAuthStore();
            return userStore.isLoggedIn;
        }
    },
    methods:{
        showDialog(){
            this.$emit('show-dialog');
        },
        fetchSummary(){
            if(this.isLoading) return;
            this.isLoading = true;
            this.$emit('fetch-summary');
        },
        toggleUpvote(newsId){
            useNewsStore().toggleUpvote(newsId);
        }
    }
};
</script>

<style scoped>
.news-item {
    padding: 1em;
}

.news-item h2 {
    margin: 0;
    font-size: 1.5em;
}

.news-item p {
    margin: .5em 0;
    text-align: start;
    font-size: 1.1em;
}

.news-item .time {
    color: #888;
}

.container{
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.summary-btn{
    font-size: 2em;
    display: none;
    cursor: pointer;
}

.summary-btn:hover{
    color: #f0ad4e;
}

.news-item:hover .summary-btn{
    display: block;
}

.texts{
    padding: 1em;
    border-radius: .5em;
    margin-right: 1em;
    width: 100%;
}

.texts:hover{
    cursor: pointer;
    background-color: rgba(0, 0, 0, 0.1);
}

.upvote-btn{
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    padding: .5em 2em;
    border-radius: 1em;
    width: 3em;
    height: 3em;
}

.upvote-btn span{
    margin-left: .25em;
    font-size: 1.2em;
    color: rgba(0,0,0,0.5);
    font-weight: bold;
}

.upvote-btn:hover{
    cursor: pointer;
    background-color: rgba(0,0,0,0.1);
}

.upvote-btn > i{
    font-size: 1.5em;
    color: rgba(0,0,0,0.5);
}

.fire-upvoted{
    color: #f6620c !important;
}

.loader {
  width: 30px;
  padding: 8px;
  aspect-ratio: 1;
  border-radius: 50%;
  background: #20A7E8;
  --_m: 
    conic-gradient(#0000 10%,#000),
    linear-gradient(#000 0 0) content-box;
  -webkit-mask: var(--_m);
          mask: var(--_m);
  -webkit-mask-composite: source-out;
          mask-composite: subtract;
  animation: l3 1s infinite linear;
}
@keyframes l3 {to{transform: rotate(1turn)}}
</style>