from flask import Flask, jsonify
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
PORT = int(os.getenv("PORT", 9876))
HOST = os.getenv("HOST", "0.0.0.0")
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 10))
TEST_SERVER_BASE_URL = os.getenv("TEST_SERVER_BASE_URL", "http://20.244.56.144/evaluation-service")
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 0.5))
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")

# Data storage for different number types
number_stores = {
    'p': [],  # prime
    'f': [],  # fibonacci
    'e': [],  # even
    'r': []   # random
}

def fetch_numbers(number_type):
    """Fetch numbers from the third-party server based on number type."""
    endpoints = {
        'p': f"{TEST_SERVER_BASE_URL}/primes",
        'f': f"{TEST_SERVER_BASE_URL}/fibo",
        'e': f"{TEST_SERVER_BASE_URL}/even",
        'r': f"{TEST_SERVER_BASE_URL}/rand"
    }
    
    if number_type not in endpoints:
        return []
    
    # Set up authorization header with the provided token
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    try:
        response = requests.get(endpoints[number_type], headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            return data.get("numbers", [])
    except (requests.RequestException, ValueError, KeyError):
        pass
    
    return []

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def update_number_store(store, new_numbers):
    """Update the number store with new unique numbers, maintaining window size."""
    # Add only unique numbers that aren't already in the store
    prev_state = store.copy()
    
    for num in new_numbers:
        if num not in store:
            store.append(num)
    
    # Keep only the most recent numbers up to WINDOW_SIZE
    if len(store) > WINDOW_SIZE:
        store[:] = store[-WINDOW_SIZE:]
    
    return prev_state

@app.route('/numbers/<number_id>', methods=['GET'])
def get_numbers(number_id):
    """Handle requests for specific number types and return the calculated average."""
    if number_id not in ['p', 'f', 'e', 'r']:
        return jsonify({"error": "Invalid number type"}), 400
    
    # Get the current state before updating
    prev_state = number_stores[number_id].copy()
    
    # Fetch new numbers from third-party server
    start_time = time.time()
    new_numbers = fetch_numbers(number_id)
    
    # Only process if we got a response within timeout
    if time.time() - start_time <= TIMEOUT:
        # Update the store with new numbers
        prev_state = update_number_store(number_stores[number_id], new_numbers)
    
    # Calculate average of current numbers
    avg = calculate_average(number_stores[number_id])
    
    # Prepare response
    response = {
        "windowPrevState": prev_state,
        "windowCurrState": number_stores[number_id],
        "numbers": new_numbers,  # response received from 3rd party server
        "avg": round(avg, 2)
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(host=HOST, port=PORT)