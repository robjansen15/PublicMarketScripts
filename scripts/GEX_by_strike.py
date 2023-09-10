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
  
def compute_weighted_gamma(ticker, num_of_strikes):
    spot_price, option_data = scrape_data(ticker)
    
    # Dropping spot price decimals
    spot_price_no_decimals = int(spot_price)
    strikes = [spot_price_no_decimals + i for i in range(-num_of_strikes, num_of_strikes + 1)]

    gamma_values = {}

    for strike in strikes:
        call_gamma_weighted = (option_data[(option_data['type'] == 'C') & (option_data['strike'] == strike)]['gamma'] * 
                               option_data[(option_data['type'] == 'C') & (option_data['strike'] == strike)]['open_interest']).sum()
        
        put_gamma_weighted = (option_data[(option_data['type'] == 'P') & (option_data['strike'] == strike)]['gamma'] * 
                              option_data[(option_data['type'] == 'P') & (option_data['strike'] == strike)]['open_interest']).sum()

        total_weighted_gamma = call_gamma_weighted - put_gamma_weighted
        gamma_values[strike] = {'Total': total_weighted_gamma, 'C': call_gamma_weighted, 'P': put_gamma_weighted * -1}

    return gamma_values

ticker = 'SPY'
num_of_strikes = 5

gamma_results = compute_weighted_gamma(ticker, num_of_strikes)

print('GEX at each strike:')
for strike, gamma in gamma_results.items():
    print(f"Strike ({strike})")
    print(f"\tTotal: {int(gamma['Total'])}")
    print(f"\t\tC: {int(gamma['C'])}")
    print(f"\t\tP: {int(gamma['P'])}")