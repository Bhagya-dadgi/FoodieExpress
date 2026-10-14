import os
from flask import Flask, render_template, request, jsonify, redirect
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="foodieexpress"
    )
    
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            image TEXT NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()



@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM foods WHERE availability = TRUE ORDER BY id DESC"
    )
    foods = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("index.html", foods=foods)


@app.route("/admin")
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all food items
    cursor.execute("SELECT * FROM foods ORDER BY id DESC")
    foods = cursor.fetchall()

    # Dashboard statistics
    cursor.execute("SELECT COUNT(*) AS total_orders FROM orders")
    total_orders = cursor.fetchone()["total_orders"]

    cursor.execute("""
        SELECT COUNT(*) AS pending_orders
        FROM orders
        WHERE order_status = 'Pending'
    """)
    pending_orders = cursor.fetchone()["pending_orders"]

    cursor.execute("""
        SELECT COUNT(*) AS delivered_orders
        FROM orders
        WHERE order_status = 'Delivered'
    """)
    delivered_orders = cursor.fetchone()["delivered_orders"]

    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) AS total_revenue
        FROM orders
        WHERE order_status = 'Delivered'
    """)
    total_revenue = cursor.fetchone()["total_revenue"]

    # Fetch the five most recent orders
    cursor.execute("""
        SELECT id, customer_name, total_amount,
               order_status, created_at
        FROM orders
        ORDER BY id DESC
        LIMIT 5
    """)
    recent_orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",
        foods=foods,
        total_orders=total_orders,
        pending_orders=pending_orders,
        delivered_orders=delivered_orders,
        total_revenue=total_revenue,
        recent_orders=recent_orders
    )

@app.route("/admin/restaurants", methods=["GET", "POST"])
def admin_restaurants():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        cuisine = request.form.get("cuisine", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        image = request.form.get("image", "").strip()

        if not name:
            cursor.close()
            conn.close()
            return "Restaurant name is required.", 400

        cursor.execute("""
            INSERT INTO restaurants
            (name, description, cuisine, address, phone, image)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, description, cuisine, address, phone, image))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/admin/restaurants")

    cursor.execute(
        "SELECT * FROM restaurants ORDER BY id DESC"
    )
    restaurants = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "restaurants.html",
        restaurants=restaurants
    )

@app.route("/restaurant/<int:restaurant_id>")
def restaurant_menu(restaurant_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM restaurants WHERE id = %s",
        (restaurant_id,)
    )
    restaurant = cursor.fetchone()

    if restaurant is None:
        cursor.close()
        conn.close()
        return "Restaurant not found", 404

    cursor.execute(
        "SELECT * FROM foods WHERE restaurant_name = %s",
        (restaurant["name"],)
    )
    foods = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "restaurant_menu.html",
        restaurant=restaurant,
        foods=foods
    )

@app.route("/add_food", methods=["POST"])
def add_food():
    name = request.form["name"].strip()
    category = request.form["category"].strip()
    price = request.form["price"]
    image = request.form["image"].strip()

    description = request.form.get("description", "").strip()
    food_type = request.form.get("food_type", "Vegetarian")
    preparation_time = request.form.get("preparation_time", 20)
    discount = request.form.get("discount", 0)
    availability = 1 if request.form.get("availability") else 0
    rating = request.form.get("rating", 4.0)
    restaurant_name = request.form.get(
        "restaurant_name", "FoodieExpress"
    ).strip()
    extra_toppings = request.form.get("extra_toppings", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO foods (
            name, category, price, image, description,
            food_type, preparation_time, discount,
            availability, rating, restaurant_name, extra_toppings
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
    """, (
        name, category, price, image, description,
        food_type, preparation_time, discount,
        availability, rating, restaurant_name, extra_toppings
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return "Food added successfully! <a href='/admin'>Go Back</a>"

@app.route("/delete_food/<int:food_id>", methods=["POST"])
def delete_food(food_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM foods WHERE id = %s",
        (food_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/admin")

@app.route("/edit_food/<int:food_id>", methods=["GET", "POST"])
def edit_food(food_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"].strip()
        category = request.form["category"].strip()
        price = request.form["price"]
        image = request.form["image"].strip()
        description = request.form.get("description", "").strip()
        food_type = request.form.get("food_type", "Vegetarian")
        preparation_time = request.form.get("preparation_time", 20)
        discount = request.form.get("discount", 0)
        availability = 1 if request.form.get("availability") else 0
        rating = request.form.get("rating", 4.0)
        restaurant_name = request.form.get(
            "restaurant_name", "FoodieExpress"
        ).strip()
        extra_toppings = request.form.get("extra_toppings", "").strip()

        cursor.execute("""
            UPDATE foods SET
                name=%s, category=%s, price=%s, image=%s,
                description=%s, food_type=%s, preparation_time=%s,
                discount=%s, availability=%s, rating=%s,
                restaurant_name=%s, extra_toppings=%s
            WHERE id=%s
        """, (
            name, category, price, image, description,
            food_type, preparation_time, discount, availability,
            rating, restaurant_name, extra_toppings, food_id
        ))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/admin")

    cursor.execute("SELECT * FROM foods WHERE id = %s", (food_id,))
    food = cursor.fetchone()

    cursor.close()
    conn.close()

    if food is None:
        return "Food item not found", 404

    return render_template("edit_food.html", food=food)



@app.route("/food/<int:food_id>")
def food_details(food_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM foods WHERE id = %s",
        (food_id,)
    )
    food = cursor.fetchone()

    cursor.close()
    conn.close()

    if food is None:
        return "Food item not found", 404

    return render_template("food_details.html", food=food)

@app.route("/place_order", methods=["POST"])
def place_order():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid order data"}), 400

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip()
    items = data.get("items", [])

    if not name or not phone or not address:
        return jsonify({"error": "Please fill in all delivery details"}), 400

    if not phone.isdigit() or len(phone) != 10:
        return jsonify({"error": "Enter a valid 10-digit phone number"}), 400

    if not isinstance(items, list) or not items:
        return jsonify({"error": "Your cart is empty"}), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        total_amount = 0
        verified_items = []

        # Get prices from MySQL, not from the browser
        for item in items:
            food_id = item.get("id")
            quantity = item.get("quantity")

            if (
                not isinstance(food_id, int)
                or isinstance(food_id, bool)
                or not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity < 1
            ):
                return jsonify({"error": "Invalid cart item"}), 400

            cursor.execute(
                "SELECT id, name, price FROM foods "
                "WHERE id = %s AND availability = TRUE",
                (food_id,)
            )
            food = cursor.fetchone()

            if food is None:
                return jsonify({
                    "error": "A food item is unavailable. Please refresh your cart."
                }), 400

            price = food["price"]
            total_amount += price * quantity

            verified_items.append({
                "id": food["id"],
                "name": food["name"],
                "price": price,
                "quantity": quantity
            })

        cursor.execute("""
            INSERT INTO orders (
                customer_name, customer_phone, delivery_address,
                total_amount, order_status
            )
            VALUES (%s, %s, %s, %s, 'Pending')
        """, (name, phone, address, total_amount))

        order_id = cursor.lastrowid

        for item in verified_items:
            cursor.execute("""
                INSERT INTO order_items (
                    order_id, food_id, food_name, quantity, price
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                order_id,
                item["id"],
                item["name"],
                item["quantity"],
                item["price"]
            ))

        conn.commit()

        return jsonify({
            "message": "Your order was placed successfully!",
            "order_id": order_id
        }), 201

    except Exception:
        if conn is not None:
            conn.rollback()

        app.logger.exception("Failed to place order")
        return jsonify({
            "error": "Unable to place your order. Please try again."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.route("/admin/orders")
def admin_orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                customer_name,
                customer_phone,
                delivery_address,
                total_amount,
                order_status,
                created_at
            FROM orders
            ORDER BY created_at DESC
        """)
        orders = cursor.fetchall()

        for order in orders:
            cursor.execute("""
                SELECT food_name, quantity, price
                FROM order_items
                WHERE order_id = %s
            """, (order["id"],))

            order["items"] = cursor.fetchall()

        return render_template("orders.html", orders=orders)

    finally:
        cursor.close()
        conn.close()


@app.route("/admin/update_order_status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    status = request.form.get("order_status", "").strip()

    print("Order ID received:", order_id)
    print("Selected status:", status)

    allowed_statuses = [
        "Pending",
        "Preparing",
        "Out for Delivery",
        "Delivered"
    ]

    if status not in allowed_statuses:
        return "Invalid order status: " + status, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id FROM orders WHERE id = %s",
            (order_id,)
        )

        if cursor.fetchone() is None:
            return "Order not found", 404

        cursor.execute(
            "UPDATE orders SET order_status = %s WHERE id = %s",
            (status, order_id)
        )

        conn.commit()

        print("Order status updated successfully!")

        return redirect("/admin/orders")

    except Exception:
        conn.rollback()
        app.logger.exception("Failed to update order status")
        return "Unable to update order status. Check the VS Code terminal.", 500

    finally:
        cursor.close()
        conn.close()



def seed_foods():
    foods = [
        (1, "Margherita Pizza", "Pizza", 199,
         "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?w=500"),
        (2, "Cheese Burger", "Burger", 149,
         "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=500"),
        (3, "Chicken Biryani", "Biryani", 249,
         "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=500"),
        (5, "Masala Dosa", "South Indian", 80,
         "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=500"),
        (6, "French Fries", "Snacks", 99,
         "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=500"),
        (7, "Chocolate Ice Cream", "Dessert", 70,
         "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=500"),
        (8, "Veg Momos", "Snacks", 120,
         "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500"),
        (9, "Pasta", "Italian", 180,
         "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=500"),
        (10, "Pancakes", "Dessert", 150,
         "https://images.unsplash.com/photo-1528207776546-365bb710ee93?w=500")
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    for food in foods:
        cursor.execute("""
            INSERT IGNORE INTO foods
            (id, name, category, price, image)
            VALUES (%s, %s, %s, %s, %s)
        """, food)

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_table()
    seed_foods()

    print(app.url_map)
    app.run(
    debug=os.environ.get("FLASK_DEBUG") == "1",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 5000))
) 
