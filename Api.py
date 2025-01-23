from fastapi import FastAPI, Request,Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ProductService import ProductService
from pydantic import BaseModel
from OrderService import OrderService
from CustomerService import CustomerService
from SalesService import SalesService
from typing import List
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
    interval_type: str | None = None


class TimeModal(BaseModel):
    from_timestamp:str="0"
    to_timestamp:str="0"
    interval_type:str=""


@app.get("/get_all_products")
async def get_all_products(product: WooCommerce):
    all_products = product_service.get_all_products_count_stat(product.params, product.interval_type)
    return all_products


@app.get("/get_all_orders")
async def get_all_orders(order: WooCommerce):
    all_orders = order_service.get_orders_week_diff(order.params, order.interval_type)
    return all_orders

@app.get('/get_all_customers_stat')
async def get_all_customers_stat(customer: WooCommerce):
    all_customers = customer_service.get_all_customers_stat(customer.params, customer.interval_type)
    return all_customers

@app.get('/get_sales_cost_diff')
async def get_sales_cost_diff(customer: WooCommerce):
    sales_cost_diff = sales_service.get_sales_cost_diff(customer.params, customer.interval_type)
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


@app.get('/get_cart_and_sales')
async def get_cart_and_sales(from_timestamp:int=0,to_timestamp:int=0,interval_type:str=""):
    cart_data,sales_data=sales_service.get_sales_and_cart_stat(from_timestamp=from_timestamp,to_timestamp=to_timestamp,interval_type=interval_type)
    return {
        'sales_data':sales_data,
        'cart_data':cart_data
    }


@app.get('/get_customer_review')
async def get_customer_review(from_timestamp:int=0,to_timestamp:int=0,interval_type:str=""):
    customer_review=customer_service.get_customer_review(from_timestamp,to_timestamp,interval_type)
    return customer_review


@app.get('/get_comp_sales_and_discount')
async def get_comp_sales_and_discount(from_timestamp:int=0,to_timestamp:int=0,interval_type:str=""):
    comp_sales_and_discount=order_service.get_sales_with_and_without_discount(from_timestamp,to_timestamp,interval_type)
    return comp_sales_and_discount


@app.get('/get_sales_and_revenue_stat')
async def get_sales_and_revenue_stat(from_timestamp:int=0,to_timestamp:int=0,interval_type:str="month"):
    sales_and_revenue_stat=sales_service.get_sales_and_revenue_stat(from_timestamp,to_timestamp,interval_type)
    return sales_and_revenue_stat


@app.get('/get_sales_based_on_country_stats')
async def get_sales_based_on_country_stats(from_timestamp:int=0,to_timestamp:int=0,interval_type:str=""):
    country_sales,state_sales=sales_service.get_sales_based_on_country(from_timestamp,to_timestamp,interval_type)
    return {
        'country_sales':country_sales,
        'state_sales':state_sales
    }


@app.get('/get_sales_based_products')
async def  get_sales_based_products(from_timestamp:int=0,to_timestamp:int=0,sort_by:str="asc",limit:int=10):
    sales_based_products=order_service.sort_sales_based_products(from_timestamp,to_timestamp,sort_by,limit)
    return JSONResponse(content=sales_based_products)


@app.post('/get_product_details_using_id')
async def get_product_details_using_id(product_id_list: List[int] = Body(...)):
    product_details=product_service.get_product_details_using_id(product_id_list)
    return product_details