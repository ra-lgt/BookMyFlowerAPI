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
        self.utc_timezone = pytz.UTC
        

    #helper functions
    def get_all_sales(self,params={}):
        all_sales = []
        page = 1

        while True:
            current_params = params.copy()
            current_params.update({
                "status": "completed",
                "page": page,
                "per_page": 100  
            })

            sales_response = requests.get(self.urls['orders_url'], auth=self.auth, params=current_params)
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
    
    def get_corresponding_type(self,timestamp,return_type="week",kind="%Y-%m-%dT%H:%M:%SZ"):
        dt_object=None
        if(return_type=="week"):
            dt_object = datetime.fromtimestamp(timestamp)

        if(return_type=="date"):
            dt_object=datetime.utcfromtimestamp(timestamp)
            dt_object=self.utc_timezone.localize(dt_object)

        # Get the name of the day (e.g., Monday, Tuesday, etc.)
        normalized_value = dt_object.strftime(kind)
        return normalized_value
    

    #main code
    

    def get_all_page_views(self):
        url = f"https://bookmyflowers.co/wp-json/custom/v1/impressions"
        auth = HTTPBasicAuth(self.application_username, self.application_password)
        views_response = requests.get(url, auth=self.auth)
        return views_response



    def get_sales_cost_diff(self, params={}, return_type=None):
        
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
        
    

    def get_sales_and_cart_stat(self,from_timestamp=( int(time.time()) - (7 * 24 * 60 * 60)),to_timestamp=int(time.time()),return_type="week"):
        cart_mapping={}
        cursor = self.connection.cursor()
        cursor.execute("""SELECT session_key,session_value,session_expiry 
                       FROM wpbk_my_flowers24_woocommerce_sessions 
                       WHERE session_expiry > %s AND session_expiry < %s""", (from_timestamp, to_timestamp))
        sessions = cursor.fetchall()
        index=0
        for session in sessions:
            decrypted_text=decrypt_php(session[1])
            products=decrypted_text.get('product',[])
            cart_mapping[index]={
                'product_count':len(products),
                'products':products,
                'timestamp':self.get_corresponding_type(timestamp=session[2],return_type="date",kind="%Y-%m-%dT%H:%M")
            }
            index+=1

        sales_data=self.get_all_sales(params={
            "after":self.get_corresponding_type(from_timestamp,return_type="date"),
            "before":self.get_corresponding_type(to_timestamp,return_type="date")})
            
        cursor.close()