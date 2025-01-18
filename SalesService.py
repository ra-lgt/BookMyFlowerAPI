import requests
from EnvirmentService import EnvirmentService
from datetime import datetime, timedelta


class SalesService(EnvirmentService):
    def get_sales_cost_diff(self, params={}, return_type=None):
        all_sales = None

        # Fetch the sales (completed orders) for this week
        if params:
            all_sales = requests.get(self.urls['orders_url'], auth=self.auth, params=params)
        else:
            all_sales = requests.get(self.urls['orders_url'], auth=self.auth, params={"status": "completed"})

        if all_sales.status_code == 200:
            # Calculate current week's sales total cost
            current_week_total_cost = sum([float(order['total']) for order in all_sales.json()])

            today = datetime.utcnow().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_last_week = start_of_week - timedelta(days=1)
            start_of_last_week = end_of_last_week - timedelta(days=6)

            # Parameters to filter orders for last week
            last_week_params = {
                "after": start_of_last_week.isoformat() + "T00:00:00",
                "before": end_of_last_week.isoformat() + "T23:59:59",
                "status": "completed"
            }

            # Request sales (completed orders) for last week
            last_week_response = requests.get(
                self.urls['orders_url'], auth=self.auth, params=last_week_params
            )

            if last_week_response.status_code == 200:
                # Calculate last week's sales total cost
                last_week_total_cost = sum([order['total'] for order in last_week_response.json()])

                # Calculate the cost difference between this week and last week
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
            else:
                return {
                    "data": "error retrieving last week sales data",
                    "status_code": last_week_response.status_code
                }

        return {
            "data": "error",
            "status_code": all_sales.status_code
        }