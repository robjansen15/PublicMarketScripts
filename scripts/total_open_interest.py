import json
import os
from datetime import timedelta, datetime

import matplotlib.pyplot as plt
import pandas as pd
import requests
from matplotlib import dates

ticker = 'SPY'

def scrape_data(ticker='SPY', save_to_file=True):
    """Scrape data from CBOE website"""
    # Request data and save it to file
    try:
        data = requests.get(
            f"https://cdn.cboe.com/api/global/delayed_quotes/options/{ticker}.json"
        )
        
        if(save_to_file):
            with open(f"{ticker}_option_data_cboe.json", "w") as f:
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

def compute_total_open_interest(ticker, option_type):
    # Assuming scrape_data returns spot price and option data DataFrame
    spot_price, option_data = scrape_data(ticker)

    # Filter data based on option type (CALL or PUT)
    option_data = option_data[option_data['type'] == option_type]

    total_open_interest = option_data['open_interest'].sum()

    print(f'Total open interest for {ticker} {option_type} options: {total_open_interest}')
    
    return total_open_interest
    
call_total_open_interest = compute_total_open_interest(ticker, 'C')
put_total_open_interest = compute_total_open_interest(ticker, 'P')

print(f'Total open interest Put/Call ratio: {put_total_open_interest/call_total_open_interest}')