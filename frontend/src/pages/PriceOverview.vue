<script setup>
import CategoryPrice from '@/components/CategoryPrice.vue';
import Categories from '@/constants/categories';
import { usePricesStore } from '@/stores/prices';
import { computed, ref, onMounted } from 'vue';

const prices = ref({});

const store = usePricesStore();
    
const categoryList = computed(() => {
    return Object.keys(Categories);
});
const isLoading = computed(() => {
    return store.isLoading;
});
const errorMessage = computed(() => {
    return store.errorMessage;
});
const updateTime = computed(() => {
    return store.updatedTime;
});


function getPriceData(category){
    return store.getPricesByCategory(category); 
}

store.fetchPrices();

// onMounted(() => {
//     store.fetchPrices();
// });

</script>
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