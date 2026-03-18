from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ── DATABASE (TEMP) ─────────────────────────────

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
cart = []
feedback = []

# ── HOME ─────────────────────────────

@app.get("/")
def home():
    return {"message": "Welcome to E-commerce API"}

# ── GET ALL PRODUCTS ─────────────────

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

# ── SEARCH PRODUCTS (FIXED) ──────────

@app.get("/products/search")
def search_products(keyword: str = Query(...)):
    result = [p for p in products if keyword.lower() in p["name"].lower()]

    if not result:
        return {"message": f"No products found for: {keyword}"}

    return {
        "keyword": keyword,
        "total_found": len(result),
        "products": result
    }

# ── SORT PRODUCTS ────────────────────

@app.get("/products/sort")
def sort_products(
    sort_by: str = Query("price"),
    order: str = Query("asc")
):
    if sort_by not in ["price", "name"]:
        raise HTTPException(status_code=400, detail="sort_by must be 'price' or 'name'")

    reverse = True if order == "desc" else False

    sorted_products = sorted(products, key=lambda x: x[sort_by], reverse=reverse)

    return {
        "sort_by": sort_by,
        "order": order,
        "products": sorted_products
    }

# ── PAGINATION ───────────────────────

@app.get("/products/page")
def paginate_products(
    page: int = Query(1, gt=0),
    limit: int = Query(2, gt=0)
):
    start = (page - 1) * limit
    end = start + limit

    total = len(products)
    total_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "limit": limit,
        "total_products": total,
        "total_pages": total_pages,
        "products": products[start:end]
    }

# ── SORT BY CATEGORY + PRICE ─────────

@app.get("/products/sort-by-category")
def sort_by_category():
    grouped = {}

    for p in products:
        grouped.setdefault(p["category"], []).append(p)

    result = []

    for category in sorted(grouped.keys()):
        sorted_items = sorted(grouped[category], key=lambda x: x["price"])
        result.extend(sorted_items)

    return {"products": result}

# ── COMBINED (SEARCH + SORT + PAGINATE) ─────────

@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    result = products

    # FILTER
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    # SORT
    reverse = True if order == "desc" else False
    if sort_by in ["price", "name"]:
        result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    # PAGINATION
    total = len(result)
    total_pages = (total + limit - 1) // limit

    start = (page - 1) * limit
    end = start + limit

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": total_pages,
        "products": result[start:end]
    }

# ── ADD PRODUCT ──────────────────────

class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

@app.post("/products")
def add_product(product: NewProduct):
    new_id = max(p["id"] for p in products) + 1
    new_product = product.dict()
    new_product["id"] = new_id

    products.append(new_product)

    return {"message": "Product added", "product": new_product}

# ── PLACE ORDER ──────────────────────

class OrderRequest(BaseModel):
    product_id: int
    quantity: int
    customer_name: str

@app.post("/orders")
def place_order(order: OrderRequest):
    product = next((p for p in products if p["id"] == order.product_id), None)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_order = {
        "order_id": len(orders) + 1,
        "customer_name": order.customer_name,
        "product": product["name"],
        "quantity": order.quantity
    }

    orders.append(new_order)

    return {"message": "Order placed", "order": new_order}

# ── SEARCH ORDERS ────────────────────

@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):
    result = [
        o for o in orders
        if customer_name.lower() in o.get("customer_name", "").lower()
    ]

    if not result:
        return {"message": f"No orders found for: {customer_name}"}

    return {
        "customer_name": customer_name,
        "total_found": len(result),
        "orders": result
    }

# ── ORDERS PAGINATION ────────────────

@app.get("/orders/page")
def paginate_orders(
    page: int = Query(1, gt=0),
    limit: int = Query(3, gt=0)
):
    start = (page - 1) * limit
    end = start + limit

    total = len(orders)
    total_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "limit": limit,
        "total_orders": total,
        "total_pages": total_pages,
        "orders": orders[start:end]
    }

# ── CART SYSTEM ──────────────────────

@app.post("/cart/add")
def add_to_cart(product_id: int = Query(...), quantity: int = Query(1)):
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    item = {
        "product_id": product_id,
        "name": product["name"],
        "quantity": quantity,
        "price": product["price"],
        "subtotal": product["price"] * quantity
    }

    cart.append(item)

    return {"message": "Added to cart", "cart": item}

@app.get("/cart")
def view_cart():
    total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "total_items": len(cart),
        "grand_total": total
    }

# ── FEEDBACK ─────────────────────────

class Feedback(BaseModel):
    customer_name: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str]

@app.post("/feedback")
def add_feedback(data: Feedback):
    feedback.append(data.dict())

    return {
        "message": "Feedback added",
        "total": len(feedback)
    }
