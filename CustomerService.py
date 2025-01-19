import requests
from EnvirmentService import EnvirmentService
from datetime import datetime, timedelta


class CustomerService(EnvirmentService):
    def __init__(self):
        super().__init__()

    def get_all_customers(self, params={}, return_type=None):
        all_customers = []
        page = 1

        while True:
            # Add page and per_page parameters for pagination
            current_params = params.copy()
            current_params.update({
                "page": page,
                "per_page": 100  # You can adjust this number as needed, up to 100
            })

            response = requests.get(self.urls['customers_url'], auth=self.auth, params=current_params)
            if response.status_code == 200:
                customers = response.json()
                all_customers.extend(customers)

                # Check headers for pagination details
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                print(f"Page {page} - Total Customers: {response.headers.get('X-WP-Total')}, Total Pages: {total_pages}")

                # If we have fetched all the pages, break the loop
                if page >= total_pages:
                    break
                else:
                    page += 1
            else:
                return {
                    "data": "Error fetching customers",
                    "status_code": response.status_code
                }

        if return_type == "count":
            current_week_total = len(all_customers)

            today = datetime.utcnow().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_last_week = start_of_week - timedelta(days=1)
            start_of_last_week = end_of_last_week - timedelta(days=6)

            # Parameters to filter customers by last week
            last_week_params = {
                "after": start_of_last_week.isoformat() + "T00:00:00",
                "before": end_of_last_week.isoformat() + "T23:59:59"
            }

            # Request customers for last week
            last_week_response = requests.get(
                self.urls['customers_url'], auth=self.auth, params=last_week_params
            )

            if last_week_response.status_code == 200:
                last_week_total = len(last_week_response.json())
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
                    "data": "Error retrieving last week data",
                    "status_code": last_week_response.status_code
                }

        return {
            "data": all_customers,
            "status_code": 200
        }
