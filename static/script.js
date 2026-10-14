let cart = JSON.parse(localStorage.getItem("foodieCart")) || [];

function displayFoods(items) {
    const foodList = document.getElementById("food-list");

    foodList.innerHTML = items.map(food => `
        <div class="food-card">
            <img
                src="${food.image}"
                alt="${food.name}"
                onclick="openFoodDetails(${food.id})"
                style="cursor: pointer;"
            >

            <h3
                onclick="openFoodDetails(${food.id})"
                style="cursor: pointer;"
            >
                ${food.name}
            </h3>

            <p>Price: ₹${food.price}</p>

            <button onclick="addToCart(${food.id})">
                Add to Cart
            </button>
        </div>
    `).join("");
}

function openFoodDetails(foodId) {
    window.location.href = `/food/${foodId}`;
}


function filterFood(category) {
    const filteredFoods = category === "All"
        ? foods
        : foods.filter(food => food.category === category);

    displayFoods(filteredFoods);
}

function addToCart(id) {
    const food = foods.find(item => item.id === id);
    const existingItem = cart.find(item => item.id === id);

    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({ ...food, quantity: 1 });
    }

    updateCart();
}

function updateCart() {
    localStorage.setItem("foodieCart", JSON.stringify(cart));
    const cartItems = document.getElementById("cart-items");

    const total = cart.reduce(
        (sum, item) => sum + item.price * item.quantity, 0
    );

    const count = cart.reduce(
        (sum, item) => sum + item.quantity, 0
    );

    document.getElementById("cart-count").textContent = count;
    document.getElementById("cart-total").textContent = total;

    if (cart.length === 0) {
        cartItems.textContent = "Your cart is empty.";
        return;
    }
    
cartItems.innerHTML = cart.map(item => `
    <div class="cart-item">
        <h4>${item.name}</h4>
        <p>Price: ₹${item.price}</p>

        <button onclick="changeQuantity(${item.id}, -1)">−</button>
        <span>${item.quantity}</span>
        <button onclick="changeQuantity(${item.id}, 1)">+</button>

        <p>Subtotal: ₹${item.price * item.quantity}</p>

        <button onclick="removeFromCart(${item.id})">
            Remove
        </button>
    </div>
`).join("");


    
}

function changeQuantity(id, change) {
    const item = cart.find(item => item.id === id);

    if (!item) return;

    item.quantity += change;

    if (item.quantity <= 0) {
        cart = cart.filter(item => item.id !== id);
    }

    updateCart();
}


async function placeOrder() {
    const name = document.getElementById("customer-name").value.trim();
    const phone = document.getElementById("customer-phone").value.trim();
    const address = document.getElementById("customer-address").value.trim();
    const message = document.getElementById("order-message");

    if (cart.length === 0) {
        message.textContent = "Please add food to your cart first.";
        return;
    }

    if (!name || !phone || !address) {
        message.textContent = "Please fill in all delivery details.";
        return;
    }

    if (!/^[0-9]{10}$/.test(phone)) {
        message.textContent = "Enter a valid 10-digit phone number.";
        return;
    }

    message.textContent = "Placing your order...";

    try {
        const response = await fetch("/place_order", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                phone: phone,
                address: address,
                items: cart.map(item => ({
                    id: Number(item.id),
                    quantity: Number(item.quantity)
                }))
            })
        });

        const result = await response.json();

        if (!response.ok) {
            message.textContent =
                result.error || "Unable to place your order.";
            return;
        }

        message.textContent =
            `Thank you, ${name}! Your order #${result.order_id} has been placed successfully.`;

        cart = [];
        updateCart();
        document.getElementById("checkout-form").reset();

    } catch (error) {
        console.error("Order error:", error);
        message.textContent =
            "Could not connect to the server. Please try again.";
    }
}



document.getElementById("search").addEventListener("input", event => {
    const query = event.target.value.toLowerCase();

    const results = foods.filter(food =>
        food.name.toLowerCase().includes(query) ||
        food.category.toLowerCase().includes(query)
    );

    displayFoods(results);
});
function clearCart() {
    if (cart.length === 0) {
        alert("Your cart is already empty!");
        return;
    }

    const confirmClear = confirm(
        "Are you sure you want to clear your cart?"
    );

    if (confirmClear) {
        cart = [];
        updateCart();
    }
}

function removeFromCart(id) {
    cart = cart.filter(item => item.id !==Number(id));
    updateCart();
}
displayFoods(foods);
updateCart();
