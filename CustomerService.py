import requests
from EnvirmentService import EnvirmentService
from datetime import datetime, timedelta
import time
from passlib.hash import phpass

class CustomerService(EnvirmentService):
    def __init__(self):
        super().__init__()

    def get_all_customers(self,params={}):
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
                return []
        return all_customers


    def get_all_customers_stat(self, params={}, interval_type=None):
        

        if interval_type == "count":
            current_week_total = len(self.get_all_customers(params))

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
            last_week_response = self.get_all_customers(last_week_params)


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
        else:
            return {
                "data": "Error retrieving last week data",
                "status_code": last_week_response
            }

    
    def get_customer_review(self,from_timestamp=( int(time.time()) - (7 * 24 * 60 * 60)),to_timestamp=int(time.time()),interval_type="week"):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT meta.comment_id,meta_key,meta_value,comment_author,comment_author_email,comment_date FROM wpbk_my_flowers24_commentmeta AS meta 
                INNER JOIN wpbk_my_flowers24_comments ON meta.comment_id=wpbk_my_flowers24_comments.comment_ID
                    WHERE meta_key='rating' AND
                    comment_date > %s AND comment_date < %s""", (self.get_corresponding_type(from_timestamp,kind="%Y-%m-%d %H:%M:%S"),self.get_corresponding_type(to_timestamp,kind="%Y-%m-%d %H:%M:%S")))
        
        comments=cursor.fetchall()
        return comments
    
    def get_customer_details(self, email):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT 
                wc_look.customer_id,
                wc_look.username,
                wc_look.first_name,
                wc_look.last_name,
                wc_look.email,
                wc_look.date_registered,
                wc_look.date_last_active,
                wc_look.country,
                wc_look.postcode,
                wc_look.city,
                wc_look.state,
                wc_look.user_id,
                comment.comment_author,
                comment.comment_author_email,
                comment.comment_date,
                comment.comment_content,
                comment.comment_approved
            FROM wpbk_my_flowers24_wc_customer_lookup AS wc_look
            LEFT JOIN wpbk_my_flowers24_comments AS comment
            ON LOWER(wc_look.email) = LOWER(comment.comment_author_email)
            WHERE wc_look.email=%s
        """, (email,))

        
        rows = cursor.fetchall()
        
        column_names = [desc[0] for desc in cursor.description]
        
        customer_details = [dict(zip(column_names, row)) for row in rows]
        
        
        return customer_details
    
    def admin_signin(self,email,password):
        cursor = self.connection.cursor()
        cursor.execute("""SELECT user_login,user_pass FROM wpbk_my_flowers24_users WHERE user_email=%s""",(email,))
        user=cursor.fetchone()
        if user:
            if phpass.verify(password,user[1]):
                return {"status_code":200,"user_login":user[0]}
            
        return {"error":"Invalid email or password","status_code":401}