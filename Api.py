from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from ProductService import ProductService
from pydantic import BaseModel
from OrderService import OrderService
from CustomerService import CustomerService
from SalesService import SalesService
app = FastAPI()

product_service = ProductService()
order_service = OrderService()
customer_service = CustomerService()
sales_service=SalesService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,  
    allow_methods=["*"], 
    allow_headers=["*"], 
)

class WooCommerce(BaseModel):
    params: dict = {}
    return_type: str | None = None



@app.post("/get_all_products")
async def get_all_products(product: WooCommerce):
    all_products = product_service.get_all_products(product.params, product.return_type)
    return all_products


@app.post("/get_all_orders")
async def get_all_orders(order: WooCommerce):
    all_orders = order_service.get_all_orders(order.params, order.return_type)
    return all_orders

@app.post('/get_all_customers')
async def get_all_customers(customer: WooCommerce):
    all_customers = customer_service.get_all_customers(customer.params, customer.return_type)
    return all_customers

@app.post('/get_sales_cost_diff')
async def get_sales_cost_diff(customer: WooCommerce):
    sales_cost_diff = sales_service.get_sales_cost_diff(customer.params, customer.return_type)
    return sales_cost_diff