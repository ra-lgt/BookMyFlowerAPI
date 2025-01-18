import requests
from EnvirmentService import EnvirmentService
from datetime import datetime, timedelta

class ProductService(EnvirmentService):
    def get_all_products(self, params={}, return_type=None):
        all_products = None

        if params:
            all_products = requests.get(self.urls["products_url"], auth=self.auth, params=params)
        else:
            all_products = requests.get(self.urls["products_url"], auth=self.auth)

        if all_products.status_code == 200:
            if return_type == "count":
                current_week_total = int(all_products.headers.get('X-WP-Total', 0))

                today = datetime.utcnow().date()
                start_of_week = today - timedelta(days=today.weekday())
                end_of_last_week = start_of_week - timedelta(days=1)
                start_of_last_week = end_of_last_week - timedelta(days=6)

                last_week_params = {
                    "after": start_of_last_week.isoformat() + "T00:00:00",
                    "before": end_of_last_week.isoformat() + "T23:59:59"
                }

                last_week_response = requests.get(
                    self.urls["products_url"], auth=self.auth, params=last_week_params
                )

                if last_week_response.status_code == 200:
                    last_week_total = int(last_week_response.headers.get('X-WP-Total', 0))
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
                else:
                    return {
                        "data": "error retrieving last week data",
                        "status_code": last_week_response.status_code
                    }

            return {
                "data": all_products.json(),
                "status_code": 200
            }

        return {
            "data": "error",
            "status_code": all_products.status_code
        }


