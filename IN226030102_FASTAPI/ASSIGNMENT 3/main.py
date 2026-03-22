from fastapi import FastAPI, HTTPException, Response, status, Query
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Initial Product Data
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

def find_product(product_id: int):
    return next((p for p in products if p['id'] == product_id), None)

# --- READ ALL ---
@app.get('/products')
def get_all_products():
    return {"products": products, "total": len(products)}

# --- Q5: PRODUCT AUDIT (Must be above {product_id}) ---
@app.get('/products/audit')
def product_audit():
    in_stock_list = [p for p in products if p['in_stock']]
    out_stock_list = [p for p in products if not p['in_stock']]
    stock_value = sum(p['price'] * 10 for p in in_stock_list)
    
    # Handle empty list case for max()
    priciest = max(products, key=lambda p: p['price']) if products else None
    
    return {
        'total_products': len(products),
        'in_stock_count': len(in_stock_list),
        'out_of_stock_names': [p['name'] for p in out_stock_list],
        'total_stock_value': stock_value,
        'most_expensive': {'name': priciest['name'], 'price': priciest['price']} if priciest else None,
    }

# --- BONUS: CATEGORY DISCOUNT (Must be above {product_id}) ---
@app.put('/products/discount')
def bulk_discount(
    category: str = Query(..., description='Category to discount'),
    discount_percent: int = Query(..., ge=1, le=99, description='% off'),
):
    updated = []
    for p in products:
        if p['category'].lower() == category.lower():
            p['price'] = int(p['price'] * (1 - discount_percent / 100))
            updated.append(p)
            
    if not updated:
        return {'message': f'No products found in category: {category}'}
    
    return {
        'message': f'{discount_percent}% discount applied to {category}',
        'updated_count': len(updated),
        'updated_products': updated,
    }

# --- READ ONE ---
@app.get('/products/{product_id}')
def get_product(product_id: int):
    product = find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# --- Q1: ADD PRODUCT (POST) ---
@app.post('/products', status_code=status.HTTP_201_CREATED)
def add_product(new_item: NewProduct):
    # Check for duplicate names
    if any(p['name'].lower() == new_item.name.lower() for p in products):
        raise HTTPException(status_code=400, detail="Product name already exists")
    
    next_id = max(p['id'] for p in products) + 1 if products else 1
    product_dict = new_item.model_dump()
    product_dict['id'] = next_id
    products.append(product_dict)
    
    return {"message": "Product added", "product": product_dict}

# --- Q2: UPDATE PRODUCT (PUT) ---
@app.put('/products/{product_id}')
def update_product(
    product_id: int, 
    price: Optional[int] = None, 
    in_stock: Optional[bool] = None
):
    product = find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if price is not None:
        product['price'] = price
    if in_stock is not None:
        product['in_stock'] = in_stock
        
    return {"message": "Product updated", "product": product}

# --- Q3: DELETE PRODUCT ---
@app.delete('/products/{product_id}')
def delete_product(product_id: int):
    product = find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    products.remove(product)
    return {"message": f"Product '{product['name']}' deleted"}