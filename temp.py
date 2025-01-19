import mysql.connector

# Replace with your database details
host = 'bookmyflowers.co'  # Use the IP address or domain
user = 'bookmyflowers_A_yadav'
password = 'CHSq6;i9pTC4'
database = 'bookmyflowers_mywesbite'

# Establish connection
connection = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

if connection.is_connected():
    print("Connected to MySQL server")

    # Create a cursor object using the connection
    cursor = connection.cursor()

    # Example query
    cursor.execute("SELECT * FROM your_table_name")
    result = cursor.fetchall()

    for row in result:
        print(row)

else:
    print("Failed to connect")

# Close the connection
cursor.close()
connection.close()
