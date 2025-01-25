import requests
from EnvirmentService import EnvirmentService
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import time
from Decryption import decrypt_php
import pytz

class SalesService(EnvirmentService):
    def __init__(self):
        super().__init__()
        

    #helper functions
    def get_all_sales(self,params={},url_type="orders_url"):
        all_sales = []
        page = 1
        sales_response=None

        while True:
            current_params = params.copy()
            current_params.update({
                "page": page,
                "per_page": 100,
                "status":"completed"
            })
            if(url_type=="orders_url"):
                sales_response = requests.get(self.urls['orders_url'], auth=self.auth, params=current_params)
            elif(url_type=="revenue_report"):
                sales_response = requests.get(self.urls['revenue_report'], auth=self.auth, params=current_params)
                return sales_response.json()

            if sales_response.status_code == 200:
                sales_data = sales_response.json()
                all_sales.extend(sales_data)

                total_pages = int(sales_response.headers.get('X-WP-TotalPages', 1))

                if page >= total_pages:
                    break
                else:
                    page += 1
            else:
                return []
        return all_sales
    

    #main code
    

    def get_all_page_views(self):
        url = f"https://bookmyflowers.co/wp-json/custom/v1/impressions"
        auth = HTTPBasicAuth(self.application_username, self.application_password)
        views_response = requests.get(url, auth=self.auth)
        return views_response



    def get_sales_cost_diff(self, params={}, interval_type=None):
        
        current_week_total_cost = sum([float(order['total']) for order in self.get_all_sales(params)])

        today = datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_last_week = start_of_week - timedelta(days=1)
        start_of_last_week = end_of_last_week - timedelta(days=6)

        last_week_params = {
            "after": start_of_last_week.isoformat() + "T00:00:00",
            "before": end_of_last_week.isoformat() + "T23:59:59",
            "status": "completed"
        }

        last_week_total_cost = sum([float(order['total']) for order in self.get_all_sales(last_week_params)])

        cost_diff = current_week_total_cost - last_week_total_cost
        percentage_change = (
            (cost_diff / last_week_total_cost) * 100 if last_week_total_cost > 0 else None
        )

        return {
            "data": {
                "current_week_total_cost": current_week_total_cost,
                "last_week_total_cost": last_week_total_cost,
                "cost_diff": cost_diff,
                "percentage_change": f"{percentage_change:+.2f}%" if percentage_change is not None else "N/A"
            },
            "status_code": 200
        }
    

    def get_category_sales(self,products_list,sales_list):
        product_category_map = {}
        for product in products_list:
            product_id = product["id"]
            categories = [cat["name"] for cat in product["categories"]]
            product_category_map[product_id] = categories

        category_sales = {}
        for order in sales_list:
            for item in order["line_items"]:
                product_id = item["product_id"]
                total = float(item["total"])
                categories = product_category_map.get(product_id, [])
                for category in categories:
                    if category not in category_sales:
                        category_sales[category] = 0
                    category_sales[category] += total

        return category_sales
        
    

    def get_sales_and_cart_stat(self,from_timestamp=( int(time.time()) - (7 * 24 * 60 * 60)),to_timestamp=int(time.time()),interval_type="week"):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT session_key,session_value,created_at 
                       FROM wpbk_my_flowers24_woocommerce_sessions 
                       WHERE created_at > %s AND created_at < %s""", (from_timestamp, to_timestamp))
        sessions = cursor.fetchall()
        cart_data=[]
        sales_data=[]
        for session in sessions:
            decrypted_text=decrypt_php(session[1])
            products=decrypted_text.get('product',[])
            cart_mapping={
                'product_count':len(products),
                'products':products,
                'timestamp':self.get_corresponding_type(timestamp=session[2],interval_type="date",kind="%Y-%m-%dT%H:%M")
            }
            cart_data.append(cart_mapping)

        all_sales=self.get_all_sales(params={
            "after":self.get_corresponding_type(from_timestamp,interval_type="date"),
            "before":self.get_corresponding_type(to_timestamp,interval_type="date")})

        for sale in all_sales:
            sale_mapping={
                'order_id':sale['id'] if 'id' in sale else -1,
                'date_created':sale['date_created'] if 'date_created' in sale else "",
                'total':sale['total'] if 'total' in sale else 0,
                'products_id':[i['product_id'] for i in sale['line_items']],
                'products_name':[i['name'] for i in sale['line_items']],
                'product_prices':[i['total'] for i in sale['line_items']],                
            }
            sales_data.append(sale_mapping)
        cursor.close()

        return cart_data,sales_data
    
    def get_sales_and_revenue_stat(self,from_timestamp=( int(time.time()) - (7 * 24 * 60 * 60)),to_timestamp=int(time.time()),interval_type="week"):
        params={
            "after":self.get_corresponding_type(from_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "before":self.get_corresponding_type(to_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "interval":interval_type
        }
        all_sales_stat=self.get_all_sales(params=params,url_type="revenue_report")

        return all_sales_stat
    

    def get_sales_based_on_country(self,from_timestamp=( int(time.time()) - (7 * 24 * 60 * 60)),to_timestamp=int(time.time()),interval_type="week"):
        params={
            "after":self.get_corresponding_type(from_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "before":self.get_corresponding_type(to_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "interval":interval_type
        }
        all_sales=self.get_all_sales(params=params)

        country_sales={}
        state_sales={}
        for sale in all_sales:
            if(sale['billing']['country'] not in country_sales):
                country_sales[sale['billing']['country']]=0
            country_sales[sale['billing']['country']]+=float(sale['total'])

            if(sale['billing']['state'] not in state_sales):
                state_sales[sale['billing']['state']]=0
            state_sales[sale['billing']['state']]+=float(sale['total'])

        return country_sales,state_sales
    

    def get_all_vendor_details(self):
        page = 1
        all_vendors = []

        while True:
            response = requests.get(self.urls['vendor_url'], headers=self.bearer_token_headers, params={"per_page": 100, "page": page})
            
            if response.status_code != 200:
                print(f"Failed to fetch data. Status Code: {response.status_code}, Response: {response.text}")
                break
            
            data = response.json()

            all_vendors.extend(data)

            if not data or len(data) < 100:
                break

            page += 1

        return all_vendors
