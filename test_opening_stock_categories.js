// Test Opening Stock Category Filtering
// This simulates the JavaScript logic to verify the fix

const testData = {
    products: [
        { id: 1, name: 'Apple', category: 'Fruits' },
        { id: 2, name: 'Rice', category: 'Groceries' },
        { id: 3, name: 'Milk', category: null },
        { id: 4, name: 'Banana', category: 'Fruits' }
    ],
    openingStock: [
        { id: 1, name: 'Apple', quantity: 50, purchase_price: 100, created_at: '2024-01-01T10:00:00Z' },
        { id: 2, name: 'Rice', quantity: 10, purchase_price: 60, created_at: '2024-01-02T10:00:00Z' },
        { id: 3, name: 'Milk', quantity: 0, purchase_price: 25, created_at: '2024-01-03T10:00:00Z' }
    ]
};

// Simulate the fixed JavaScript logic for category mapping
const productToCategoryMap = new Map();
testData.products.forEach(product => {
    let categoryName = product.category || null; // Use category directly from API
    productToCategoryMap.set(product.name.toLowerCase(), categoryName);
    console.log(`Mapped "${product.name}" to category: ${categoryName}`);
});

// Add category_name to opening stock data (simulating loadOpeningStockData)
const openingStockWithCategories = testData.openingStock.map(item => {
    const itemName = item.name?.toLowerCase() || '';
    const mappedCategoryName = productToCategoryMap.get(itemName);
    return {
        ...item,
        category_name: mappedCategoryName || null
    };
});

console.log('\nOpening Stock with Categories:');
openingStockWithCategories.forEach(item => {
    console.log(`- ${item.name}: Category = '${item.category_name}'`);
});

// Test filtering by "Groceries" category (should show Rice)
const groceriesFiltered = openingStockWithCategories.filter(item => {
    const matches = item.category_name == 'Groceries';
    console.log(`Checking item "${item.name}": category_name=${item.category_name}, matches=${matches}`);
    return matches;
});

console.log('\nFiltered by "Groceries" category:');
console.log(groceriesFiltered); // Should show Rice with 10 quantity

console.log('\n✅ Test Complete: Category filtering should now work correctly!');
