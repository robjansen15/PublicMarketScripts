import json
import os
from datetime import timedelta, datetime
import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np

def scrape_data(ticker='SPY', save_to_file=True):
    """Scrape data from CBOE website"""
    # Request data and save it to file
    try:
        data = requests.get(
            f"https://cdn.cboe.com/api/global/delayed_quotes/options/_{ticker}.json"
        )
        
        if(save_to_file):
            with open(f"data/{ticker}_option_data_cboe.json", "w") as f:
                json.dump(data.json(), f)

    except ValueError:
        data = requests.get(
            f"https://cdn.cboe.com/api/global/delayed_quotes/options/{ticker}.json"
        )
        
    data = pd.DataFrame.from_dict(data.json())

    spot_price = data.loc["current_price", "data"]
    option_data = pd.DataFrame(data.loc["options", "data"])

    return spot_price, fix_option_data(option_data)

def fix_option_data(data):
    """
    Fix option data columns.
    From the name of the option derive type of option, expiration and strike price
    """
    data["type"] = data.option.str.extract(r"\d([A-Z])\d")
    data["strike"] = data.option.str.extract(r"\d[A-Z](\d+)\d\d\d").astype(int)
    data["expiration"] = data.option.str.extract(r"[A-Z](\d+)").astype(str)
    # Convert expiration to datetime format
    data["expiration"] = pd.to_datetime(data["expiration"], format="%y%m%d")
    return data

def compute_total_open_interest(ticker, option_type, option_data):
    # Filter data based on option type (CALL or PUT)
    option_data = option_data[option_data['type'] == option_type]

    total_open_interest = option_data['open_interest'].sum()

    print(f'Total open interest for {ticker} {option_type} options: {total_open_interest}')
    
    return total_open_interest

def plot_open_interest(option_data, spot_price):
    # Filter data for CALL and PUT options separately
    call_data = option_data[option_data['type'] == 'C']
    put_data = option_data[option_data['type'] == 'P']

    # Define the strike price range (+/- 10% of spot price)
    strike_range = [spot_price * 0.9, spot_price * 1.1]

    # Filter CALL and PUT data within the strike price range
    call_data_filtered = call_data[(call_data['strike'] >= strike_range[0]) & (call_data['strike'] <= strike_range[1])]
    put_data_filtered = put_data[(put_data['strike'] >= strike_range[0]) & (put_data['strike'] <= strike_range[1])]

    # Group data by strike price and calculate total open interest for each
    call_open_interest_by_strike = call_data_filtered.groupby('strike')['open_interest'].sum()
    put_open_interest_by_strike = put_data_filtered.groupby('strike')['open_interest'].sum()

    # Create a bar chart for both CALL and PUT options
    plt.figure(figsize=(12, 6))

    # Plot CALL open interest as bars in green
    plt.bar(call_open_interest_by_strike.index, call_open_interest_by_strike.values, label='CALL Open Interest', color='green', width=0.4)

    # Plot PUT open interest as bars in red (negative values)
    plt.bar(put_open_interest_by_strike.index, -put_open_interest_by_strike.values, label='PUT Open Interest', color='red', width=0.4)

    # Add a vertical black bar at the spot price
    plt.axvline(x=spot_price, color='black', linestyle='-.', label='Spot Price', linewidth=2)

    # Add a horizontal black bar at 0
    plt.axhline(y=0, color='black', linestyle='-', linewidth=2)

    # Triple the number of X-axis labels
    x_ticks = np.linspace(strike_range[0], strike_range[1], 40)
    plt.xticks(x_ticks, ['{:.2f}'.format(x) for x in x_ticks], rotation=90)

    plt.xlabel('Strike Price')
    plt.ylabel('Total Open Interest')
    plt.title('Open Interest by Strike Price (CALL in green, PUT in red) within +/- 10% of Spot Price')
    plt.legend()

    plt.tight_layout()
    plt.show()

ticker = 'SPY'
spot_price, option_data = scrape_data(ticker)

call_total_open_interest = compute_total_open_interest(ticker, 'C', option_data)
put_total_open_interest = compute_total_open_interest(ticker, 'P', option_data)

print(f'Total open interest Put/Call ratio: {put_total_open_interest/call_total_open_interest}')

plot_open_interest(option_data, spot_price)

print('Total open interest is expressed as the number of contracts outstanding at the end of the day.')
