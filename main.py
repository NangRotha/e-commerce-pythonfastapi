from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import os
import models
import auth
from database import engine, get_db

# Create tables
from sqlalchemy import inspect
inspector = inspect(engine)

# Drop and recreate tables for fresh start (remove this in production)
# models.Base.metadata.drop_all(bind=engine)

# Create all tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-Commerce App")

# Ensure directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("templates/admin", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Middleware to add user to template context
@app.middleware("http")
async def add_user_to_context(request: Request, call_next):
    token = request.cookies.get("access_token")
    user = None
    if token:
        try:
            from fastapi.security import HTTPAuthorizationCredentials
            token_value = token.replace("Bearer ", "")
            token_obj = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_value)
            db = next(get_db())
            user = await auth.get_current_user(token_obj, db)
            db.close()
        except Exception as e:
            pass
    
    request.state.current_user = user
    response = await call_next(request)
    return response

def get_current_user_for_template(request: Request):
    return getattr(request.state, 'current_user', None)

# Create default admin and sample data
def create_default_data(db: Session):
    # Create admin user
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        admin_user = models.User(
            username="admin",
            email="admin@example.com",
            hashed_password=auth.get_password_hash("admin123"),
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print("✓ Default admin created: admin / admin123")
    
    # Create sample users
    if db.query(models.User).filter(models.User.is_admin == False).count() == 0:
        sample_users = [
            models.User(
                username="john_doe",
                email="john@example.com",
                hashed_password=auth.get_password_hash("password123"),
                is_admin=False
            ),
            models.User(
                username="jane_smith",
                email="jane@example.com",
                hashed_password=auth.get_password_hash("password123"),
                is_admin=False
            ),
            models.User(
                username="mike_wilson",
                email="mike@example.com",
                hashed_password=auth.get_password_hash("password123"),
                is_admin=False
            ),
        ]
        for user in sample_users:
            db.add(user)
        db.commit()
        print("✓ Sample users created")
    
    # Create sample products
    if db.query(models.Product).count() == 0:
        sample_products = [
            models.Product(
                name="iPhone 15 Pro Max",
                description="Apple's latest flagship with A17 Pro chip, 48MP camera, and titanium design. Features a 6.7-inch Super Retina XDR display with ProMotion.",
                price=1199.99,
                stock=45,
                image_url="https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=400",
                category="Electronics"
            ),
            models.Product(
                name="Samsung Galaxy S24 Ultra",
                description="Latest Samsung flagship with AI capabilities, 200MP camera, and S Pen integration. 6.8-inch Dynamic AMOLED 2X display.",
                price=1299.99,
                stock=32,
                image_url="https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400",
                category="Electronics"
            ),
            models.Product(
                name="MacBook Pro M3",
                description="Apple MacBook Pro with M3 chip, 14-inch Liquid Retina XDR display, 16GB RAM, 512GB SSD. Perfect for professionals.",
                price=1999.99,
                stock=28,
                image_url="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400",
                category="Electronics"
            ),
            models.Product(
                name="Nike Air Max 270",
                description="Nike Air Max 270 features the biggest heel Air unit yet for maximum comfort. Breathable mesh upper with sleek design.",
                price=149.99,
                stock=120,
                image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
                category="Sports"
            ),
            models.Product(
                name="Adidas Ultraboost 22",
                description="Adidas Ultraboost running shoes with responsive Boost midsole and Primeknit upper for ultimate comfort and energy return.",
                price=179.99,
                stock=85,
                image_url="https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=400",
                category="Sports"
            ),
            models.Product(
                name="Sony WH-1000XM5",
                description="Industry-leading noise cancellation with exceptional sound quality. 30-hour battery life and advanced features.",
                price=399.99,
                stock=67,
                image_url="https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400",
                category="Electronics"
            ),
            models.Product(
                name="Dyson V15 Detect",
                description="Powerful cordless vacuum with laser technology that reveals invisible dust. Intelligent optimization and LCD display.",
                price=699.99,
                stock=23,
                image_url="https://images.unsplash.com/photo-1558317374-067fb5f30001?w=400",
                category="Home"
            ),
            models.Product(
                name="Instant Pot Duo Plus",
                description="9-in-1 multi-use programmable pressure cooker. Sauté, steam, slow cook, and more. Perfect for quick, healthy meals.",
                price=129.99,
                stock=156,
                image_url="https://images.unsplash.com/photo-1585515325310-e94f5b7f6bc5?w=400",
                category="Home"
            ),
            models.Product(
                name="Levi's 501 Jeans",
                description="Original Levi's 501 button-fly jeans. Classic straight fit with iconic styling. 100% cotton denim.",
                price=89.99,
                stock=200,
                image_url="https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=400",
                category="Fashion"
            ),
            models.Product(
                name="The North Face Jacket",
                description="Waterproof, windproof jacket with breathable fabric. Perfect for outdoor activities in any weather.",
                price=249.99,
                stock=42,
                image_url="https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400",
                category="Fashion"
            ),
        ]
        for product in sample_products:
            db.add(product)
        db.commit()
        print("✓ Sample products created")
    
    # Create sample orders with real data
    if db.query(models.Order).count() == 0:
        users = db.query(models.User).filter(models.User.is_admin == False).all()
        products = db.query(models.Product).all()
        
        if users and products:
            # Create orders for the last 30 days
            for i in range(20):
                order_date = datetime.utcnow() - timedelta(days=i)
                user = users[i % len(users)]
                
                # Random order status based on date
                if i < 5:
                    status = "delivered"
                elif i < 10:
                    status = "shipped"
                elif i < 15:
                    status = "paid"
                else:
                    status = "pending"
                
                # Random number of items per order
                num_items = (i % 3) + 1
                order_items = []
                total_amount = 0
                
                for j in range(num_items):
                    product = products[(i + j) % len(products)]
                    quantity = (i % 5) + 1
                    price = product.price
                    item_total = price * quantity
                    total_amount += item_total
                    order_items.append({
                        "product_id": product.id,
                        "quantity": quantity,
                        "price": price
                    })
                
                # Create order
                order = models.Order(
                    user_id=user.id,
                    total_amount=total_amount,
                    status=status,
                    shipping_address=f"{user.username}'s Address, {123 + i} Main St, City {i}",
                    created_at=order_date
                )
                db.add(order)
                db.flush()
                
                # Create order items
                for item in order_items:
                    order_item = models.OrderItem(
                        order_id=order.id,
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                        price=item["price"]
                    )
                    db.add(order_item)
                    
                    # Update stock
                    product = db.query(models.Product).filter(models.Product.id == item["product_id"]).first()
                    if product:
                        product.stock -= item["quantity"]
            
            db.commit()
            print("✓ Sample orders created")
    
    # Create cart items for some users
    if db.query(models.CartItem).count() == 0:
        users = db.query(models.User).filter(models.User.is_admin == False).limit(3).all()
        products = db.query(models.Product).limit(5).all()
        
        for user in users:
            for product in products[:3]:
                cart_item = models.CartItem(
                    user_id=user.id,
                    product_id=product.id,
                    quantity=(user.id % 3) + 1
                )
                db.add(cart_item)
        db.commit()
        print("✓ Sample cart items created")

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    create_default_data(db)
    print("\n" + "="*60)
    print("🚀 E-COMMERCE APPLICATION STARTED SUCCESSFULLY!")
    print("="*60)
    print("📍 Application URL: http://localhost:8000")
    print("🔑 Admin Login: admin / admin123")
    print("👥 Demo Users:")
    print("   - john_doe / password123")
    print("   - jane_smith / password123")
    print("   - mike_wilson / password123")
    print("="*60 + "\n")

# ==================== PUBLIC ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    products = db.query(models.Product).order_by(desc(models.Product.created_at)).limit(8).all()
    current_user = get_current_user_for_template(request)
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "products": products,
        "current_user": current_user
    })

@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request, category: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Product)
    if category:
        query = query.filter(models.Product.category == category)
    products = query.all()
    categories = db.query(models.Product.category).distinct().all()
    current_user = get_current_user_for_template(request)
    return templates.TemplateResponse("products.html", {
        "request": request, 
        "products": products,
        "categories": [c[0] for c in categories if c[0]],
        "selected_category": category,
        "current_user": current_user
    })

@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    current_user = get_current_user_for_template(request)
    return templates.TemplateResponse("product_detail.html", {
        "request": request, 
        "product": product,
        "current_user": current_user
    })

# ==================== API ENDPOINTS ====================

@app.get("/api/cart/count")
async def get_cart_count(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user:
        return {"count": 0}
    
    count = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).count()
    return {"count": count}

# ==================== AUTH ROUTES ====================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    current_user = get_current_user_for_template(request)
    return templates.TemplateResponse("login.html", {"request": request, "current_user": current_user})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, username, password)
    if not user:
        current_user = get_current_user_for_template(request)
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid credentials",
            "current_user": current_user
        })
    
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, path="/")
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    current_user = get_current_user_for_template(request)
    return templates.TemplateResponse("register.html", {"request": request, "current_user": current_user})

@app.post("/register")
async def register(request: Request, email: str = Form(...), username: str = Form(...), 
                   password: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()
    
    if existing_user:
        current_user = get_current_user_for_template(request)
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Username or email already exists",
            "current_user": current_user
        })
    
    new_user = models.User(
        email=email,
        username=username,
        hashed_password=auth.get_password_hash(password),
        is_admin=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RedirectResponse(url="/login", status_code=302)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token", path="/")
    return response

# ==================== USER ROUTES ====================

@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    cart_items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).all()
    total = sum(item.quantity * item.product.price for item in cart_items)
    return templates.TemplateResponse("cart.html", {
        "request": request, 
        "cart_items": cart_items, 
        "total": total,
        "current_user": current_user
    })

@app.post("/cart/add")
async def add_to_cart(request: Request, product_id: int = Form(...), quantity: int = Form(1), 
                      db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Check if product exists and has stock
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product or product.stock < quantity:
        return RedirectResponse(url=f"/product/{product_id}", status_code=302)
    
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id,
        models.CartItem.product_id == product_id
    ).first()
    
    if cart_item:
        if cart_item.quantity + quantity <= product.stock:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = product.stock
    else:
        cart_item = models.CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.add(cart_item)
    
    db.commit()
    return RedirectResponse(url="/cart", status_code=302)

@app.post("/cart/update")
async def update_cart(request: Request, item_id: int = Form(...), quantity: int = Form(...), 
                      db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.user_id == current_user.id
    ).first()
    
    if cart_item:
        if quantity <= 0:
            db.delete(cart_item)
        else:
            product = cart_item.product
            if quantity <= product.stock:
                cart_item.quantity = quantity
        db.commit()
    
    return RedirectResponse(url="/cart", status_code=302)

@app.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    cart_items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).all()
    if not cart_items:
        return RedirectResponse(url="/cart", status_code=302)
    
    total = sum(item.quantity * item.product.price for item in cart_items)
    return templates.TemplateResponse("checkout.html", {
        "request": request, 
        "cart_items": cart_items, 
        "total": total,
        "current_user": current_user
    })

@app.post("/checkout")
async def create_order(request: Request, shipping_address: str = Form(...), db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    cart_items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    total_amount = sum(item.quantity * item.product.price for item in cart_items)
    
    # Create order
    order = models.Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address=shipping_address,
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Create order items and update stock
    for cart_item in cart_items:
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=cart_item.product.price
        )
        db.add(order_item)
        
        # Update stock
        product = cart_item.product
        product.stock -= cart_item.quantity
        db.delete(cart_item)
    
    db.commit()
    
    return RedirectResponse(url=f"/orders", status_code=302)

@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).order_by(desc(models.Order.created_at)).all()
    # Load items for each order
    for order in orders:
        order.items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order.id).all()
    return templates.TemplateResponse("orders.html", {
        "request": request, 
        "orders": orders,
        "current_user": current_user
    })

# ==================== ADMIN ROUTES ====================

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    
    # Check if user is admin
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=302)
    
    # Calculate total revenue
    total_revenue = db.query(func.sum(models.Order.total_amount)).filter(
        models.Order.status.in_(['paid', 'shipped', 'delivered'])
    ).scalar() or 0
    
    # Get order counts by status
    total_orders = db.query(models.Order).count()
    completed_orders = db.query(models.Order).filter(models.Order.status == 'delivered').count()
    pending_orders = db.query(models.Order).filter(models.Order.status == 'pending').count()
    shipped_orders = db.query(models.Order).filter(models.Order.status == 'shipped').count()
    delivered_orders = db.query(models.Order).filter(models.Order.status == 'delivered').count()
    
    # New orders in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_orders = db.query(models.Order).filter(models.Order.created_at >= week_ago).count()
    
    # Product stats
    total_products = db.query(models.Product).count()
    low_stock_products = db.query(models.Product).filter(models.Product.stock < 10).count()
    
    # User stats
    total_users = db.query(models.User).filter(models.User.is_admin == False).count()
    new_users = db.query(models.User).filter(
        models.User.is_admin == False,
        models.User.created_at >= week_ago
    ).count()
    
    # Recent orders with user info
    recent_orders = db.query(models.Order).order_by(desc(models.Order.created_at)).limit(10).all()
    
    # Top selling products
    top_products_query = db.query(
        models.Product,
        func.sum(models.OrderItem.quantity).label('total_sold')
    ).join(models.OrderItem).group_by(models.Product.id).order_by(desc(func.sum(models.OrderItem.quantity))).limit(5).all()
    
    top_products_data = []
    for product, total_sold in top_products_query:
        product.total_sold = total_sold
        top_products_data.append(product)
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_users": total_users,
        "new_orders": new_orders,
        "low_stock_products": low_stock_products,
        "new_users": new_users,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
        "recent_orders": recent_orders,
        "top_products": top_products_data,
        "current_user": current_user
    })

@app.get("/admin/products", response_class=HTMLResponse)
async def admin_products(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=302)
    
    products = db.query(models.Product).order_by(desc(models.Product.created_at)).all()
    return templates.TemplateResponse("admin/products.html", {
        "request": request, 
        "products": products,
        "current_user": current_user
    })

@app.post("/admin/products/create")
async def create_product(request: Request, name: str = Form(...), description: str = Form(...), 
                         price: float = Form(...), stock: int = Form(...), 
                         image_url: str = Form(...), category: str = Form(...),
                         db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=302)
    
    product = models.Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        image_url=image_url,
        category=category
    )
    db.add(product)
    db.commit()
    
    return RedirectResponse(url="/admin/products", status_code=302)

@app.post("/admin/products/delete/{product_id}")
async def delete_product(request: Request, product_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=302)
    
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
    
    return RedirectResponse(url="/admin/products", status_code=302)

@app.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=302)
    
    orders = db.query(models.Order).order_by(desc(models.Order.created_at)).all()
    return templates.TemplateResponse("admin/orders.html", {
        "request": request, 
        "orders": orders,
        "current_user": current_user
    })

@app.post("/admin/orders/update/{order_id}")
async def update_order_status(request: Request, order_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=302)
    
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order:
        order.status = status
        db.commit()
    
    return RedirectResponse(url="/admin/orders", status_code=302)

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_for_template(request)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=302)
    
    users = db.query(models.User).filter(models.User.is_admin == False).order_by(desc(models.User.created_at)).all()
    return templates.TemplateResponse("admin/users.html", {
        "request": request, 
        "users": users,
        "current_user": current_user
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)