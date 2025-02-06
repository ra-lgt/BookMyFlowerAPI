import requests
from EnvirmentService import EnvirmentService
from datetime import datetime, timedelta

class ProductService(EnvirmentService):
    def __init__(self):
        super().__init__()

    def get_all_products(self,params={}):
        all_products = []
        page = 1
        while True:
            current_params = params.copy()
            current_params.update({
                "page": page,
                "per_page": 100  
            })

            response = requests.get(self.urls["products_url"], auth=self.auth, params=current_params)
            if response.status_code == 200:
                products = response.json()
                all_products.extend(products)
                
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                else:
                    page += 1
            else:
                return []

        return all_products

    def get_all_products_count_stat(self, params={}, interval_type=None):
            

            if interval_type == "count":
                current_week_total = len(self.get_all_products(params))

                today = datetime.utcnow().date()
                start_of_week = today - timedelta(days=today.weekday())
                end_of_last_week = start_of_week - timedelta(days=1)
                start_of_last_week = end_of_last_week - timedelta(days=6)

                last_week_params = {
                    "after": start_of_last_week.isoformat() + "T00:00:00",
                    "before": end_of_last_week.isoformat() + "T23:59:59"
                }


                last_week_total = len(self.get_all_products(last_week_params))
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

            return {
                "data": [],
                "status_code": 200
            }
    
    def get_product_details_using_id(self,product_id_list,included_keys={}):
        params={}
        if(product_id_list!=[]):
            params.update({"include[]":product_id_list})
        params.update(included_keys)
            
        product_details=self.get_all_products(params)
        return product_details
    
    def check_products_for_alerts(self):
        all_products=self.get_all_products()
        store_details={}
        for product in all_products:
            if((product['stock_quantity']!=None and product['stock_quantity']<=10) or product['stock_status']=="outofstock"):
                store_id=product.get('store',{}).get('id')
                if(store_id not in store_details):
                    store_details[store_id]=[]
                store_details[store_id].append(product)
                
        return store_details