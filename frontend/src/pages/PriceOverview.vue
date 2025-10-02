<template>
    <div class="wrapper">
        <h1>各類商品物價概覽</h1>
        <h3 v-if="!isLoading" class="subtitle">資料更新時間：{{updateTime}}</h3>
        <div class="prices">
            <CategoryPrice class="category" v-for="category in categoryList" :key="category"
                :category="category" :isLoading="isLoading" :errorMessage="errorMessage" :priceData="getPriceData(category)"></CategoryPrice>
        </div>
    </div>
</template>

<script>
import CategoryPrice from '@/components/CategoryPrice.vue';
import Categories from '@/constants/categories';
import { usePricesStore } from '@/stores/prices';

export default {
    name: 'PriceOverview',
    data() {
        return {
            prices: {},
        };
    },
    components: {
        CategoryPrice
    },
    computed: {
        categoryList() {
            return Object.keys(Categories);
        },
        isLoading(){
            const store = usePricesStore();
            return store.isLoading;
        },
        errorMessage(){
            const store = usePricesStore();
            return store.errorMessage;
        },
        updateTime(){
            const store = usePricesStore();
            return store.updatedTime;
        }
    },
    methods:{
        getPriceData(category){
            const store = usePricesStore();
            return store.getPricesByCategory(category);
        }    
    },
    created() {
        const store = usePricesStore();
        store.fetchPrices();
    }
};
</script>

<style scoped>
.wrapper{
    padding: 3em 5em;
    background: #f3f3f3;
    min-height: calc(100vh - 4.5em);
    height: calc(100% - 4.5em);
    box-sizing: border-box;
}
.prices{
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
}
.category{
    margin: 1em;
    flex-grow: 1;
}
.subtitle{
    font-weight: normal;
    margin-top: .5em;
}
</style>