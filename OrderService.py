import requests
from EnvirmentService import EnvirmentService
from datetime import datetime, timedelta
import json

class OrderService(EnvirmentService):
    def __init__(self):
        super().__init__()
    def get_all_orders(self, params={}, interval_type=None):
            all_orders = []
            page = 1

            while True:
                current_params = params.copy()
                current_params.update({
                    "page": page,
                    "per_page": 100  
                })

                response = requests.get(self.urls['orders_url'], auth=self.auth, params=current_params)
                if response.status_code == 200:
                    orders = response.json()
                    all_orders.extend(orders)

                    total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                    print(f"Page {page} - Total Orders: {response.headers.get('X-WP-Total')}, Total Pages: {total_pages}")

                    if page >= total_pages:
                        break
                    else:
                        page += 1
                else:
                    return []
            return all_orders

          
    
    def get_orders_week_diff(self, params={}, interval_type=None):
           all_orders = self.get_all_orders(params, interval_type)
           if interval_type == "count":
            current_week_total = len(all_orders)

            today = datetime.utcnow().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_last_week = start_of_week - timedelta(days=1)
            start_of_last_week = end_of_last_week - timedelta(days=6)

            last_week_params = {
                "after": start_of_last_week.isoformat() + "T00:00:00",
                "before": end_of_last_week.isoformat() + "T23:59:59"
            }
            if 'status' in params:
                last_week_params['status'] = params['status']

            last_week_response=self.get_all_orders(last_week_params)


            last_week_total = len(last_week_response)
            percentage_change = (
                ((current_week_total - last_week_total) / last_week_total) * 100
                if last_week_total > 0 else None
            )

            return {
                "data": {
                    "current_week_total": current_week_total,
                    "last_week_total": last_week_total,
                    "percentage_change": f"{percentage_change:+.2f}%" if percentage_change is not None else "N/A"
                },
                "status_code": 200
            }
           
    def get_sales_with_and_without_discount(self,from_timestamp,to_timestamp,interval_type):
        params={
            "after":self.get_corresponding_type(from_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "before":self.get_corresponding_type(to_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "status":"completed",
            "fields":'id,date_created,total,discount_total'
        }
        all_orders=self.get_all_orders(params=params)

        return all_orders
    

    def sort_sales_based_products(self,from_timestamp,to_timestamp,sort_by="asc",limit=10):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT id,status,order_id,product_id,SUM(product_gross_revenue) AS total_sold FROM wpbk_my_flowers24_wc_orders
                       INNER JOIN wpbk_my_flowers24_wc_order_product_lookup ON wpbk_my_flowers24_wc_orders.id=wpbk_my_flowers24_wc_order_product_lookup.order_id
                       WHERE date_created > %s AND date_created < %s
                       AND status='wc-completed'
                       GROUP BY product_id
                       ORDER BY total_sold {}
                       LIMIT %s
                       """.format(sort_by), (self.get_corresponding_type(from_timestamp,kind="%Y-%m-%d %H:%M:%S"),self.get_corresponding_type(to_timestamp,kind="%Y-%m-%d %H:%M:%S"),limit))
        sales_data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]  # Get column names
        sales_data_dict = [dict(zip(columns, row)) for row in sales_data]
        sales_data_json = json.dumps(sales_data_dict)
        return sales_data_json