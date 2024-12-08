from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import mysql.connector
from io import StringIO
from faker import Faker
import math
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
fake = Faker()

# MySQL connection setup
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",  # Change if needed
        user="flask_user",
        password="flask_password",
        database="dataset_db"
    )

# Serve the HTML form on the root URL
@app.route('/')
def index():
    try:
        # Pagination settings (page and per_page)
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Connect to MySQL
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Count the total number of records in the transactions table
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_records = cursor.fetchone()['COUNT(*)']

        # Calculate total pages
        total_pages = math.ceil(total_records / per_page)

        # Calculate the offset for the SQL query
        offset = (page - 1) * per_page

        # Query the transactions table with LIMIT and OFFSET for pagination
        cursor.execute(
            "SELECT * FROM transactions LIMIT %s OFFSET %s",
            (per_page, offset)
        )
        transactions = cursor.fetchall()

        cursor.close()
        conn.close()

        # Render the template and pass the transactions data, pagination info
        return render_template(
            'index.html',
            transactions=transactions,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            total_records=total_records
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to accept dataset URL
@app.route('/upload', methods=['POST'])
def upload_data():
    # Get URL from the incoming request
    url = request.json.get('url')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Step 1: Download the CSV dataset from the URL
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download data from the URL"}), 400

        # Step 2: Load the JSON data
        data = response.json()

        # Step 3: Write data into MySQL
        conn = get_db_connection()
        cursor = conn.cursor()

        # Iterate over the incoming JSON data and insert into MySQL
        for transaction in data:
            cursor.execute(
                "INSERT INTO transactions (date, transaction_id, item, amount, location) "
                "VALUES (%s, %s, %s, %s, %s)",
                (transaction['date'], transaction['transaction_id'], transaction['item'],
                 transaction['amount'], transaction['location'])
            )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Data uploaded successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New API endpoint to fetch all transactions
@app.route('/api/transactions', methods=['GET'])
def get_all_transactions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to fetch all transactions from the database
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()

        cursor.close()
        conn.close()

        # Return the transactions as a JSON response
        return jsonify(transactions), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate/<int:num_transactions>', methods=['GET'])
def generate_data(num_transactions):
    data = [generate_random_transaction() for _ in range(num_transactions)]
    return jsonify(data)

# Function to generate random data
def generate_random_transaction():
    ITEMS = ['Laptop', 'Smartphone', 'Headphones', 'Keyboard', 'Monitor']
    LOCATIONS = ['New York', 'San Francisco', 'Los Angeles', 'Chicago', 'Houston']

    transaction_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    item = random.choice(ITEMS)
    amount = round(random.uniform(10, 1000), 2)  # Random amount between 10 and 1000
    location = random.choice(LOCATIONS)
    date = fake.date_this_year()  # Random date this year

    transaction = {
        "date": date.strftime('%Y-%m-%d'),
        "transaction_id": transaction_id,
        "item": item,
        "amount": amount,
        "location": location
    }

    return transaction
if __name__ == "__main__":
    app.run(debug=True, port=5001)