import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import numpy as np

def fetch_and_save_stock_data(ticker_symbol, days_back=30, interval='15m', save_dir='data'):
    # Define the start and end dates for the data
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

    # Fetch the historical data using yfinance
    data = yf.download(ticker_symbol, start=start_date, end=end_date, interval=interval)

    # Extract only the close prices
    close_prices = data['Close']

    # Create a data folder if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Save the data to a JSON file
    filename = os.path.join(save_dir, f'{ticker_symbol}_{interval}_{days_back}d.json')
    close_prices.to_json(filename, orient='columns')

    print("Data saved successfully!")
    
    return filename

def compute_standard_deviations(filename):
    # Load data from the file
    with open(filename, 'r') as f:
        data = json.load(f)

    # Extract prices
    prices = np.array(list(data.values()))

    # Calculate mean
    mean = np.mean(prices)

    # Calculate standard deviation
    std_dev = np.std(prices)

    # Calculate upper and lower bounds for the first standard deviation
    std_dev_1_upper = mean + std_dev
    std_dev_1_lower = mean - std_dev

    # Calculate upper and lower bounds for the second standard deviation
    std_dev_2_upper = mean + 2*std_dev
    std_dev_2_lower = mean - 2*std_dev

    # Return results in a dictionary
    return {
        "MEAN": mean,
        "1 STD Upper": round(std_dev_1_upper, 2),
        "1 STD Lower": round(std_dev_1_lower, 2),
        "2 STD Upper": round(std_dev_2_upper, 2),
        "2 STD Lower": round(std_dev_2_lower, 2)
    }

days_back = 30

filename = fetch_and_save_stock_data('SPY', days_back, interval='15m', save_dir='data')
results = compute_standard_deviations(filename)

print(f"Mean: {results['MEAN']}")
print(f"1 STD: {results['1 STD Upper']} - {results['1 STD Lower']}")
print(f"2 STD: {results['2 STD Upper']} - {results['2 STD Lower']}")