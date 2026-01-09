## Mini Project: Real-World Inventory Management System

### Project Overview

**Scenario:** You're building an inventory management system for a retail store chain. The system needs to track products across multiple warehouses, manage stock levels, handle product movements, and generate reports.

**Real-World Requirements:**
- Track products with SKU, name, category, price
- Manage multiple warehouse locations
- Record stock levels per warehouse
- Log product movements (incoming, outgoing, transfers)
- Alert on low stock levels
- Generate inventory reports
- Track product suppliers
- Handle batch operations

### Database Schema

```
Products Table:
- id (Primary Key)
- sku (Unique)
- name
- category
- price
- reorder_level
- supplier_id
- created_at

Warehouses Table:
- id (Primary Key)
- name
- location
- capacity
- manager_name

Inventory Table:
- id (Primary Key)
- product_id (Foreign Key)
- warehouse_id (Foreign Key)
- quantity
- last_updated

Movements Table:
- id (Primary Key)
- product_id (Foreign Key)
- warehouse_id (Foreign Key)
- movement_type (IN/OUT/TRANSFER)
- quantity
- reference_number
- notes
- created_at

Suppliers Table:
- id (Primary Key)
- name
- contact_email
- phone
- address
```

### Key Features to Implement

**Product Management:**
- Add/Update/Delete products
- Search products by SKU, name, or category
- Get products by supplier
- Get low stock products

**Warehouse Management:**
- Add/Update/Delete warehouses
- Get warehouse capacity utilization
- Get products in specific warehouse

**Inventory Operations:**
- Receive stock (incoming)
- Ship stock (outgoing)
- Transfer stock between warehouses
- Adjust stock levels
- Get current stock by product
- Get stock history

**Reporting:**
- Total inventory value
- Stock levels across all warehouses
- Movement history
- Low stock alerts
- Warehouse utilization report
- Product turnover rate


### Implementation Guidelines

**Step 1: Database Setup**
- Create all tables with proper relationships
- Add indexes on frequently queried columns (SKU, product_id, warehouse_id)
- Implement foreign key constraints

**Step 2: Core CRUD Operations**
- Implement product management
- Implement warehouse management
- Implement supplier management

**Step 3: Inventory Logic**
- Implement stock receiving with validation
- Implement stock shipping with quantity checks
- Implement transfers with source/destination validation
- Add transaction logging for audit trail

**Step 4: Business Rules**
- Prevent negative stock levels
- Validate warehouse capacity
- Check reorder levels and generate alerts
- Ensure SKU uniqueness

**Step 5: Reporting**
- Aggregate inventory values
- Calculate warehouse utilization
- Generate movement reports with filters
- Create low stock alerts

**Step 6: Advanced Features**
- Add batch operations for bulk imports
- Implement stock forecasting based on movement history
- Add role-based access (if needed)
- Create scheduled reports

### Sample Implementation Structure

```python
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from datetime import datetime
from typing import Optional, List

app = FastAPI(
    title="Inventory Management System",
    description="Complete inventory management for retail stores",
    version="1.0.0"
)

# Database setup with SQLite (can be replaced with PostgreSQL/MySQL)
engine = create_engine("sqlite:///./inventory.db")

def init_database():
    # Create all tables
    pass

# Product endpoints
@app.post("/products")
def create_product(sku: str, name: str, category: str, price: float, 
                   reorder_level: int, supplier_id: int):
    pass

@app.get("/products")
def get_products(category: Optional[str] = None, low_stock: bool = False):
    pass

@app.get("/products/{product_id}")
def get_product(product_id: int):
    pass

# Warehouse endpoints
@app.post("/warehouses")
def create_warehouse(name: str, location: str, capacity: int, manager_name: str):
    pass

@app.get("/warehouses/{warehouse_id}/inventory")
def get_warehouse_inventory(warehouse_id: int):
    pass

# Inventory operations
@app.post("/inventory/receive")
def receive_stock(product_id: int, warehouse_id: int, quantity: int, 
                  reference_number: str, notes: Optional[str] = None):
    pass

@app.post("/inventory/ship")
def ship_stock(product_id: int, warehouse_id: int, quantity: int,
               reference_number: str, notes: Optional[str] = None):
    pass

@app.post("/inventory/transfer")
def transfer_stock(product_id: int, from_warehouse_id: int, 
                   to_warehouse_id: int, quantity: int, notes: Optional[str] = None):
    pass

@app.get("/inventory/product/{product_id}")
def get_product_inventory(product_id: int):
    pass

# Reporting endpoints
@app.get("/reports/inventory-value")
def get_inventory_value():
    pass

@app.get("/reports/low-stock")
def get_low_stock_report(threshold: Optional[int] = None):
    pass

@app.get("/reports/movements")
def get_movement_history(product_id: Optional[int] = None,
                         warehouse_id: Optional[int] = None,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None):
    pass

@app.get("/reports/warehouse-utilization")
def get_warehouse_utilization():
    pass

# Supplier endpoints
@app.post("/suppliers")
def create_supplier(name: str, contact_email: str, phone: str, address: str):
    pass

@app.get("/suppliers/{supplier_id}/products")
def get_supplier_products(supplier_id: int):
    pass
```

### Extension Ideas

1. **Multi-tenant Support:** Add company/organization isolation
2. **Barcode Integration:** Add barcode scanning endpoints
3. **Notifications:** Email/SMS alerts for low stock
4. **Analytics Dashboard:** Add endpoints for charts and graphs
5. **Order Management:** Integrate with purchase orders
6. **Return Handling:** Add product return workflows
7. **Batch Tracking:** Track products by batch/lot numbers
8. **Expiry Management:** Track expiration dates for perishables
9. **Cost Tracking:** Add FIFO/LIFO cost calculations
10. **Integration APIs:** Connect with e-commerce platforms

---

## Best Practices Summary

### API Design
- Use meaningful endpoint names
- Follow REST conventions
- Return appropriate HTTP status codes
- Provide clear error messages
- Include pagination for large datasets

### Database Operations
- Always validate input data
- Use transactions for multi-step operations
- Handle database errors gracefully
- Close connections properly
- Use parameterized queries to prevent SQL injection

### Error Handling
```python
from fastapi import HTTPException

if not found:
    raise HTTPException(status_code=404, detail="Resource not found")

if invalid_data:
    raise HTTPException(status_code=400, detail="Invalid input data")

if unauthorized:
    raise HTTPException(status_code=401, detail="Unauthorized access")
```

### Documentation
- Add docstrings to endpoints
- Use descriptive parameter names
- Provide example requests/responses
- Document business rules

### Performance
- Use database indexes
- Implement pagination
- Cache frequently accessed data
- Optimize queries
- Use connection pooling

---

## Resources & Next Steps

### Learning Resources
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Core Tutorial: https://docs.sqlalchemy.org/
- REST API Design: https://restfulapi.net/
- SQL Best Practices: https://www.sqlstyle.guide/

### Deployment Considerations
- Use environment variables for configuration
- Implement logging
- Add health check endpoints
- Use production-grade database (PostgreSQL, MySQL)
- Implement authentication and authorization
- Add rate limiting
- Set up monitoring and alerts


---
