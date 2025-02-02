from fastapi import FastAPI, Request,Body,Form, File, UploadFile
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


class AdminSigninRequest(BaseModel):
    email: str
    password: str


class TimeModal(BaseModel):
    from_timestamp:str="0"
    to_timestamp:str="0"
    interval_type:str=""
@app.post("/admin_signin")
async def admin_signin(data: AdminSigninRequest):
    return customer_service.admin_signin(data.email,data.password)


@app.get("/get_all_products")
async def get_all_products(params:dict={},interval_type:str=""):
    all_products = product_service.get_all_products_count_stat(params, interval_type)
    return all_products


@app.get("/get_orders_week_diff")
async def get_orders_week_diff(params:dict={},interval_type:str=""):
    all_orders = order_service.get_orders_week_diff(params, interval_type)
    return all_orders

@app.post("/get_all_orders")
async def get_all_orders(params:dict={},interval_type:str=""):
    all_orders = order_service.get_all_orders(params, interval_type)
    return all_orders

@app.get('/get_all_customers_stat')
async def get_all_customers_stat(params:dict={},interval_type:str=""):
    all_customers = customer_service.get_all_customers_stat(params, interval_type)
    return all_customers

@app.get('/get_all_customers')
async def get_all_customers(params:dict={}):
    all_customers = customer_service.get_all_customers(params)
    return all_customers


@app.get('/get_customer_details')
async def get_customer_details(email:str=""):
    email=email.strip()
    customer_details=customer_service.get_customer_details(email=email)
    user_id = next((i['user_id'] for i in customer_details if i['user_id'] is not None), -1)
    customer_ids=[i['customer_id'] for i in customer_details]
    all_order_data=order_service.get_all_orders()

    all_order_data_filter = [
    i for i in all_order_data
    if (
        i.get('customer_id') in customer_ids or
        i.get('billing', {}).get('email', '').strip() == email or
        i.get('shipping', {}).get('email', '').strip() == email
    )
]
    cart_data=sales_service.get_sales_and_cart_stat(0,2147483647,only_cart=True)

    all_cart_data_filtered = [
        i for i in cart_data
        if any((int(j) in customer_ids or int(j)==user_id) for j in i.get('customer_id', []))
    ]
    included_keys={
        "_fields": "name,date_created,stock_status,price,total_sales,images,store,average_rating",
    }

    for i in range(len(all_cart_data_filtered)):
        product_details=product_service.get_product_details_using_id(product_id_list=all_cart_data_filtered[i]['products'],included_keys=included_keys)
        all_cart_data_filtered[i]['product_details']=product_details


    return {
        'customer_details':customer_details,
        'order_data':all_order_data_filter,
        'cart_data':all_cart_data_filtered
    }


@app.get('/get_sales_cost_diff')
async def get_sales_cost_diff(params:dict={},interval_type:str=""):
    sales_cost_diff = sales_service.get_sales_cost_diff(params, interval_type)
    return sales_cost_diff

@app.get('/get_all_category_based_sales')
async def get_all_category_based_sales():
    all_products=product_service.get_all_products()
    all_sales=sales_service.get_all_sales(params={"status":"completed"})

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
async def get_product_details_using_id(product_id_list: List[int] = Body(...),included_keys:dict={}):
    product_details=product_service.get_product_details_using_id(product_id_list,included_keys)
    return product_details


@app.get('/get_all_vendors')
async def get_all_vendors():
    all_vendors=sales_service.get_all_vendor_details()
    return all_vendors

@app.post('/create_kanban_card')
async def create_kanban_card(data:dict=Body(...)):
    return sales_service.create_or_update_kanban_card(data)


@app.post("/update_kanban_board")
async def update_kanban(
    title: str = Form(...),
    due_date: str = Form(...),
    label: str = Form(...),
    comment: str = Form(...),
    card_id: str = Form(...),
    attachment: UploadFile = File(...)
):
    return await sales_service.update_kanban_board(kanban_details={
        "card_title":title,
        "due_date":due_date,
        "label":label,
        "comment":comment,
        "card_id":card_id,  
        "attachment":attachment
    })
@app.get('/get_kanban_data')
async def get_kanban_data():
    return sales_service.kanban_board_data()