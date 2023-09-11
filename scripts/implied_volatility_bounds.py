import json
import os
from datetime import timedelta, datetime
import pandas as pd
import requests

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

def average_iv(num_of_strikes, spot_price, option_data):
    spot_price_no_decimals = int(spot_price)

    # Generate the list of strikes around the spot price
    strikes = [spot_price_no_decimals + i for i in range(-num_of_strikes, num_of_strikes + 1)]

    # Filter the option_data for the given strikes
    relevant_options = option_data[option_data['strike'].isin(strikes)]

    # Return the average implied volatility
    return relevant_options['iv'].mean()

ticker = 'SPX'
num_of_strikes = 10

spot_price, option_data = scrape_data(ticker)
average_iv = average_iv(num_of_strikes, spot_price, option_data)

average_iv_std1 = average_iv / 15.87;
average_iv_std2 = average_iv / 15.87 * 2;

# Calculate the bounds for 1 standard deviation
upper_bound_std1 = spot_price * (1 + average_iv_std1)
lower_bound_std1 = spot_price * (1 - average_iv_std1)

# Calculate the bounds for 2 standard deviations
upper_bound_std2 = spot_price * (1 + average_iv_std2)
lower_bound_std2 = spot_price * (1 - average_iv_std2)

print(f"1 STD: {lower_bound_std1} - {upper_bound_std1}")
print(f"2 STD: {lower_bound_std2} - {upper_bound_std2}")