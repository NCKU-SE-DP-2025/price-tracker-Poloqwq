<script setup>
import { usePricesStore } from '@/stores/prices';
import Categories from '@/constants/categories';
import TrendingTable from '@/components/TrendingTable.vue';
import TrendingChart from '@/components/TrendingChart.vue';
import { ref, computed, watch } from 'vue';

const store = usePricesStore();
const selectedCategory = ref('');
const selectedProduct = ref('');
const productList = ref([]);
const productData = ref(null);

const categoryKeys = computed(() => {
    return Object.keys(Categories); 
});
const products = computed(() => {
    return selectedCategory.value ? store.getPricesByCategory(selectedCategory.value) : [];
});


function categoryName(category) {
    return Categories[category];
}

watch(selectedCategory, ()=>{
    selectedProduct.value = '';
    productList.value = store.getProductList(selectedCategory.value);
    productData.value = null;
})
watch(selectedProduct, ()=>{console.log(selectedProduct)});

store.fetchPrices();

</script>
<template>
    <div class="wrapper">
        <h1>物價趨勢</h1>
        <div class="content">
            <div class="selects">

                <select v-model="selectedCategory">
                    <option disabled value="">請選擇商品類別</option>
                    <option v-for="category in categoryKeys" :key="category" :value="category">{{
                        categoryName(category)}}</option>
                </select>
                <select v-model="selectedProduct">
                    <option disabled value="">請選擇商品</option>
                    <option v-for="product in products" :key="product.產品名稱" :value="product">{{ product.產品名稱 }}</option>
                </select>
            </div>
            <div v-if="selectedProduct" class="visualize">
                <TrendingChart v-if="selectedProduct" :data="selectedProduct"></TrendingChart>
                <TrendingTable v-if="selectedProduct" :data="selectedProduct"></TrendingTable>
            </div>
        </div>
    </div>
</template>



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
    margin-top: 2em;
    background-color: #fff;
    border-radius: 1em;
    padding: 2em;
    width: 100%;
}


.selects {
    display: flex;
    justify-content: flex-start;
}

.selects>select {
    padding: .5em;
    font-size: 1.1em;
    margin-right: 1em;
    border-radius: .5em;
    border: 1px solid #ccc;
    outline: none;
    cursor: pointer;
    appearance: auto !important;
}

.visualize > * {
    flex: 1 1 50%;
    box-sizing: border-box;
    padding: 1em;
}
</style>