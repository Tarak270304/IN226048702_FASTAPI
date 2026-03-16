from fastapi import FastAPI, Query ,HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ── Temporary data — acting as our database ─────────────────────

products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook', 'price': 99, 'category': 'Stationery', 'in_stock': True},
    {'id': 3, 'name': 'USB Hub', 'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set', 'price': 49, 'category': 'Stationery', 'in_stock': True},
    {'id': 5, 'name': 'Laptop Stand', 'price': 1299, 'category': 'Electronics', 'in_stock': True},
    {'id': 6, 'name': 'Mechanical Keyboard', 'price': 2499, 'category': 'Electronics', 'in_stock': True},
    {'id': 7, 'name': 'Webcam', 'price': 1899, 'category': 'Electronics', 'in_stock': False}
]

orders = []
feedback = []
cart = []

# ── Home ──────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Welcome to our E-commerce API"}

# ── All Products ───────────────────────────────────

@app.get("/products")
def get_all_products():
    return {"products": products, "total": len(products)}

# ── Filter Products ─────────────────────────────────

@app.get("/products/filter")
def filter_products(
    category: str = Query(None),
    max_price: int = Query(None),
    min_price: int = Query(None),
    in_stock: bool = Query(None)
):

    result = products

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return {"filtered_products": result, "count": len(result)}

# ── Category Filter ─────────────────────────────────

@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):

    result = [p for p in products if p["category"].lower() == category_name.lower()]

    if not result:
        return {"error": "No products found"}

    return {"category": category_name, "products": result}

# ── In Stock Products ───────────────────────────────

@app.get("/products/instock")
def get_instock_products():

    instock = [p for p in products if p["in_stock"]]

    return {"in_stock_products": instock, "count": len(instock)}

# ── Store Summary ───────────────────────────────────

@app.get("/store/summary")
def store_summary():

    total = len(products)
    instock = sum(p["in_stock"] for p in products)
    out = total - instock
    categories = list({p["category"] for p in products})

    return {
        "store_name": "My E-commerce Store",
        "total_products": total,
        "in_stock": instock,
        "out_of_stock": out,
        "categories": categories
    }

# ── Search Products ─────────────────────────────────

@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    result = [p for p in products if keyword.lower() in p["name"].lower()]

    return {"results": result, "count": len(result)}

# ── Deals ───────────────────────────────────────────

@app.get("/products/deals")
def get_deals():

    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {"best_deal": cheapest, "premium_pick": expensive}

# ================= DAY 2 =============================

@app.get("/products/summary")
def product_summary():

    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])

    categories = list(set(p["category"] for p in products))

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {"name": expensive["name"], "price": expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }

# ── PRODUCT AUDIT (DAY 4 TASK) ──────────────────────

@app.get("/products/audit")
def product_audit():

    in_stock_list = [p for p in products if p["in_stock"]]
    out_stock_list = [p for p in products if not p["in_stock"]]

    stock_value = sum(p["price"] * 10 for p in in_stock_list)

    priciest = max(products, key=lambda p: p["price"])

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_list),
        "out_of_stock_names": [p["name"] for p in out_stock_list],
        "total_stock_value": stock_value,
        "most_expensive": {
            "name": priciest["name"],
            "price": priciest["price"]
        }
    }

# ── BULK DISCOUNT (BONUS) ───────────────────────────

@app.put("/products/discount")
def bulk_discount(
    category: str = Query(...),
    discount_percent: int = Query(..., ge=1, le=99)
):

    updated = []

    for p in products:
        if p["category"].lower() == category.lower():
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append(p)

    if not updated:
        return {"message": f"No products found in category: {category}"}

    return {
        "message": f"{discount_percent}% discount applied to {category}",
        "updated_count": len(updated),
        "updated_products": updated
    }

# ── ADD PRODUCT (POST) ──────────────────────────────

class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

@app.post("/products")
def add_product(product: NewProduct):

    for p in products:
        if p["name"].lower() == product.name.lower():
            return {"error": "Product already exists"}

    next_id = max(p["id"] for p in products) + 1

    new_product = {
        "id": next_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock
    }

    products.append(new_product)

    return {"message": "Product added", "product": new_product}

# ── UPDATE PRODUCT (PUT) ────────────────────────────

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    price: Optional[int] = None,
    in_stock: Optional[bool] = None
):

    for p in products:
        if p["id"] == product_id:

            if price is not None:
                p["price"] = price

            if in_stock is not None:
                p["in_stock"] = in_stock

            return {"message": "Product updated", "product": p}

    return {"error": "Product not found"}

# ── DELETE PRODUCT ──────────────────────────────────

@app.delete("/products/{product_id}")
def delete_product(product_id: int):

    for p in products:
        if p["id"] == product_id:

            products.remove(p)

            return {"message": f"Product '{p['name']}' deleted"}

    return {"error": "Product not found"}

# ── PRODUCT PRICE ───────────────────────────────────

@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for p in products:
        if p["id"] == product_id:
            return {"name": p["name"], "price": p["price"]}

    return {"error": "Product not found"}

# ── GET PRODUCT ─────────────────────────────────────

@app.get("/products/{product_id}")
def get_product(product_id: int):

    for p in products:
        if p["id"] == product_id:
            return {"product": p}

    return {"error": "Product not found"}

# ── FEEDBACK MODEL ──────────────────────────────────

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback)
    }

# ── BULK ORDER ──────────────────────────────────────

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str
    contact_email: str
    items: List[OrderItem]

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})

        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})

        else:
            subtotal = product["price"] * item.quantity
            total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": total
    }

# ── BONUS ORDER SYSTEM ──────────────────────────────

class OrderRequest(BaseModel):
    product_id: int
    quantity: int

@app.post("/orders")
def place_order(order: OrderRequest):

    product = next((p for p in products if p["id"] == order.product_id), None)

    if not product:
        return {"error": "Product not found"}

    new_order = {
        "order_id": len(orders) + 1,
        "product": product["name"],
        "quantity": order.quantity,
        "status": "pending"
    }

    orders.append(new_order)

    return {"message": "Order placed", "order": new_order}

@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}

    return {"error": "Order not found"}

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}

    return {"error": "Order not found"}
# ── ADD TO CART ──────────────────────────────


@app.post("/cart/add")
def add_to_cart(product_id: int = Query(...), quantity: int = Query(1, gt=0)):

    product = next((p for p in products if p["id"] == product_id), None)

    # product not found
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    existing = next((item for item in cart if item["product_id"] == product_id), None)

    if existing:
        existing["quantity"] += quantity
        existing["subtotal"] = existing["quantity"] * existing["unit_price"]

        return {
            "message": "Cart updated",
            "cart_item": existing
        }

    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": product["price"] * quantity
    }

    cart.append(cart_item)

    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }
# ── VIEW CART ──────────────────────────────

@app.get("/cart")
def view_cart():

    if not cart:
        return {"message": "Cart is empty"}

    grand_total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }
# ── REMOVE ITEM FROM CART ─────────────────────

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):

    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": f"{item['product_name']} removed from cart"}

    raise HTTPException(status_code=404, detail="Item not found in cart")
# ── CHECKOUT CART ─────────────────────────────

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


@app.post("/cart/checkout")
def checkout_cart(data: CheckoutRequest):

    if not cart:
        raise HTTPException(status_code=400, detail="CART_EMPTY")

    placed_orders = []
    total = 0

    for item in cart:

        order = {
            "order_id": len(orders) + 1,
            "customer_name": data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "subtotal": item["subtotal"],
            "delivery_address": data.delivery_address
        }

        orders.append(order)
        placed_orders.append(order)

        total += item["subtotal"]

    cart.clear()

    return {
        "message": "Checkout successful",
        "orders_placed": placed_orders,
        "grand_total": total
    }
# ── VIEW ALL ORDERS ───────────────────────────

@app.get("/orders")
def view_orders():

    return {
        "orders": orders,
        "total_orders": len(orders)
    }
