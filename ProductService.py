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

    def get_all_products_count_stat(self, params={}, return_type=None):
            

            if return_type == "count":
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
