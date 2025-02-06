import requests
from EnvirmentService import EnvirmentService
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import time
from Decryption import decrypt_php
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
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
        params.update({
            "status": "completed"
        })
        
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
                categories = product_category_map.get(product_id, [])
                for category in categories:
                    if category not in category_sales:
                        category_sales[category] = 0
                    category_sales[category] += 1

        return category_sales
        
    

    def get_sales_and_cart_stat(self,from_timestamp=( int(time.time()) - (7 * 24 * 60 * 60)),to_timestamp=int(time.time()),interval_type="week",only_cart=False):
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
                'customer_id':decrypted_text.get('customer',[]),
                'timestamp':self.get_corresponding_type(timestamp=session[2],interval_type="date",kind="%Y-%m-%dT%H:%M")
            }
            cart_data.append(cart_mapping)
        if(only_cart):
            return cart_data

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
                'customer_id':sale.get('customer_id',-1),          
                'status':sale.get('status','')     
            }
            sales_data.append(sale_mapping)
        cursor.close()

        return cart_data,sales_data
    
    def get_sales_and_revenue_stat(self,from_timestamp=( int(time.time()) - (7 * 24 * 60 * 60)),to_timestamp=int(time.time()),interval_type="week"):
        params={
            "after":self.get_corresponding_type(from_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "before":self.get_corresponding_type(to_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "interval":interval_type,
            'status':'completed'
        }
        all_sales_stat=self.get_all_sales(params=params,url_type="revenue_report")

        return all_sales_stat
    

    def get_sales_based_on_country(self,from_timestamp=( int(time.time()) - (7 * 24 * 60 * 60)),to_timestamp=int(time.time()),interval_type="week"):
        params={
            "after":self.get_corresponding_type(from_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "before":self.get_corresponding_type(to_timestamp,kind="%Y-%m-%d %H:%M:%S"),
            "interval":interval_type,
            'status':'completed'
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
    

    def get_store_details_using_id(self,store_id):
        response = requests.get(f"{self.urls['store_url']}/{store_id}", auth=self.auth)
        return response.json()
    

    def create_or_update_kanban_card(self, card_details):
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM wpbk_my_flowers24_kanban_cards WHERE card_id = %s
        """, (card_details.get('card_id', None),))

        count = cursor.fetchone()[0]

        if count > 0:
            cursor.execute("""
                UPDATE wpbk_my_flowers24_kanban_cards
                SET board_name = %s, card_title = %s, due_date = %s, label = %s, comment = %s, attachment = %s
                WHERE card_id = %s
            """, (
                card_details.get('board_name', None),
                card_details.get('card_title', None),
                card_details.get('due_date', None),
                card_details.get('label', None),
                card_details.get('comment', None),
                card_details.get('attachment', None), 
                card_details.get('card_id', None)
            ))
        else:
            # Insert new card
            cursor.execute("""
                INSERT INTO wpbk_my_flowers24_kanban_cards (card_id, board_name, card_title, due_date, label, comment, attachment)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                card_details.get('card_id', None),
                card_details.get('board_name', None),
                card_details.get('card_title', None),
                card_details.get('due_date', None),
                card_details.get('label', None),
                card_details.get('comment', None),
                card_details.get('attachment', None)  
            ))

        self.connection.commit()
        cursor.close()

        
        return {"status_code": 200, "msg": "Card created successfully"}
    

    async def update_kanban_board(self,kanban_details):
        cursor=self.connection.cursor()

        attachment=kanban_details.get('attachment')

        file_content=await attachment.read()

        encoded_content = base64.b64encode(file_content).decode('utf-8')

        cursor.execute("""
                    UPDATE wpbk_my_flowers24_kanban_cards
                       SET
                        card_title = %s,
                        due_date = %s,
                        label = %s,
                        comment = %s,
                        attachment = %s
                       """,(kanban_details.get('card_title'),kanban_details.get('due_date'),kanban_details.get('label'),kanban_details.get('comment'),encoded_content))
        
        self.connection.commit()
        self.connection.close()
        return {"status_code": 200, "msg": "Card updated successfully"}
    

    def kanban_board_data(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM wpbk_my_flowers24_kanban_cards
        """)

        columns = [desc[0] for desc in cursor.description]  # Get column names
        kanban_data = []

        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            
            formatted_data = {
                "id": row_dict.get("board_name", " ") or " ",
                "title": row_dict.get("board_name", " ") or " ",
                "item": [
                    {
                        "id": row_dict.get("card_id", " ") or " ",
                        "title": row_dict.get("card_title", " ") or " ",
                        "comments": row_dict.get("comment", " ") or " ",
                        "badge-text": row_dict.get("label", " ") or " ",
                        "badge": "success",
                        "due-date": row_dict.get("due_date", " ") or " ",
                        "image": row_dict.get("attachment", " ") or " ",
                        "assigned": (row_dict.get("assigned") or "").split(","),  
                        "members": (row_dict.get("members") or "").split(",")  
                    }
                ]
            }
            
            kanban_data.append(formatted_data)

        cursor.close()


        return kanban_data
    
    def get_all_notifications(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM wpbk_my_flowers24_notifications
            WHERE is_viewed = 0
        """)
        notifications = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        notification_data = []
        for row in notifications:
            row_dict = dict(zip(columns, row))
            notification_data.append(row_dict)
        cursor.close()
        return notification_data
    

    def update_notification_status_as_read(self,notification_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE wpbk_my_flowers24_notifications
            SET is_viewed = 1
            WHERE id = %s
        """, (notification_id,))
        self.connection.commit()
        cursor.close()
        return {"status_code": 200, "msg": "Notification updated successfully"}
    

    def post_alert_mail_config(self, data):
        cursor = self.connection.cursor()

        query = """
        INSERT INTO wpbk_my_flowers24_email_alerts (sender_email, sender_password, alert_select, email_subject, body_content)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            sender_email = VALUES(sender_email),
            sender_password = VALUES(sender_password),
            email_subject = VALUES(email_subject),
            body_content = VALUES(body_content)
        """

        values = (
            data.get("sender_email"),
            data.get("sender_password"),  
            data.get("alert_select"),
            data.get("email_subject"),
            data.get("body_content")
        )

        try:
            cursor.execute(query, values)
            self.connection.commit()  
            return {"status": "success", "message": "Alert mail config saved or updated", "affected_rows": cursor.rowcount}
        except Exception as e:
            self.connection.rollback()  
            return {"status": "error", "message": str(e)}
        finally:
            cursor.close()



    def get_all_alert_config(self):
        cursor=self.connection.cursor()
        cursor.execute("""
                        SELECT * FROM wpbk_my_flowers24_email_alerts
                        """)
        alert_config=cursor.fetchall()
        cursor.close()
        column_names = [desc[0] for desc in cursor.description]
        alert_config = [dict(zip(column_names, row)) for row in alert_config]
        return alert_config
    

    def get_details_for_vendor_id(self,vendor_id):
        response = requests.get(f"{self.urls['store_url']}/{vendor_id}", auth=self.auth)
        return response.json()
    

    def send_mail_alert(self,product,alter_dict,alert_type):
        alter_dict['body_content']=alter_dict['body_content'].format(
            product_name = product.get('name'),
            product_stock_quantity = product.get('stock_quantity'),
            product_stock_status = product.get('stock_status'),
            product_image = f'<img src="{(product.get("images") or [{}])[0].get("src")}" />'


        )
        vendor_details=self.get_details_for_vendor_id(product.get('store',{}).get('id',""))
        email=vendor_details.get('email')

        message = MIMEMultipart('alternative')
        message['Subject'] = alter_dict.get('email_subject')
        message["From"] = alter_dict.get('sender_email')
        message["To"] = email

        html_mail = MIMEText(alter_dict.get('body_content',''), 'html')
        message.attach(html_mail)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(alter_dict.get('sender_email'), alter_dict.get('sender_password'))
        server.sendmail(alter_dict.get('sender_email'), email, message.as_string())
        server.quit()

        print("Mail sent")




