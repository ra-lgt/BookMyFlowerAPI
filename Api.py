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


class TimeModal(BaseModel):
    from_timestamp:int=0
    to_timestamp:int=0
    return_type:str=""


@app.post("/get_all_products")
async def get_all_products(product: WooCommerce):
    all_products = product_service.get_all_products_count_stat(product.params, product.return_type)
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

@app.get('/get_all_category_based_sales')
async def get_all_category_based_sales():
    all_products=product_service.get_all_products()
    all_sales=sales_service.get_all_sales()

    category_based_sales=sales_service.get_category_sales(all_products,all_sales)
    return category_based_sales

#deprecated
@app.get('/get_page_views_and_sales_stat')
async def get_page_views_and_sales_stat():
    page_view=sales_service.get_all_page_views()
    return page_view


@app.post('/get_cart_and_sales')
async def get_cart_and_sales(time_modal:TimeModal):
    cart_and_sales=sales_service.get_sales_and_cart_stat(from_timestamp=time_modal.from_timestamp,to_timestamp=time_modal.to_timestamp,return_type=time_modal.return_type)
    return cart_and_sales