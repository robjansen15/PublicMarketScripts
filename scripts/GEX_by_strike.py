import json
import os
from datetime import timedelta, datetime

import matplotlib.pyplot as plt
import pandas as pd
import requests
from matplotlib import dates

def scrape_data(ticker='SPY', save_to_file=True):
    """Scrape data from CBOE website"""
    # Request data and save it to file
    try:
        data = requests.get(
            f"https://cdn.cboe.com/api/global/delayed_quotes/options/_{ticker}.json"
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
  
def compute_GEX(ticker, num_of_strikes):
    spot_price, option_data = scrape_data(ticker)
    
    option_data = option_data[option_data['open_interest'] != 0.0]
    # Dropping spot price decimals
    spot_price_no_decimals = int(spot_price)
    strikes = [spot_price_no_decimals + i for i in range(-num_of_strikes, num_of_strikes + 1)]

    GEX_values = {}

    for strike in strikes:
        call_gamma_weighted = (option_data[(option_data['type'] == 'C') & (option_data['strike'] == strike)]['gamma'] *
                               option_data[(option_data['type'] == 'C') & (option_data['strike'] == strike)]['delta'] *
                               spot_price *
                               option_data[(option_data['type'] == 'C') & (option_data['strike'] == strike)]['open_interest']).sum()
        
        put_gamma_weighted = (option_data[(option_data['type'] == 'P') & (option_data['strike'] == strike)]['gamma'] *
                              option_data[(option_data['type'] == 'P') & (option_data['strike'] == strike)]['delta'] *
                              spot_price *
                              option_data[(option_data['type'] == 'P') & (option_data['strike'] == strike)]['open_interest']).sum()

        total_GEX = call_gamma_weighted + put_gamma_weighted
        GEX_values[strike] = {'Total': int(total_GEX), 'C': int(call_gamma_weighted), 'P': int(put_gamma_weighted)}

    return GEX_values


def plot_gamma_results(gamma_results):
    # Filter out results where total gamma is zero.
    filtered_results = {strike: gamma for strike, gamma in gamma_results.items() if gamma['Total'] != 0}

    strikes = list(filtered_results.keys())
    total_gammas = [gamma['Total'] for gamma in filtered_results.values()]

    # Plotting
    plt.figure(figsize=(12,7))

    # Plotting total gamma
    bars = plt.bar(strikes, total_gammas, alpha=0.8)

    # Color bars and add text label
    for bar in bars:
        yval = bar.get_height()
        if yval != 0:  # Only add a label if the gamma value is not 0.
            plt.text(bar.get_x() + bar.get_width()/2, yval + 5, round(yval, 2), ha='center', va='bottom')
        if yval > 0:
            bar.set_color('green')
        else:
            bar.set_color('red')

    # Adding a horizontal line at y=0
    plt.axhline(y=0, color='black', linestyle='--')
    
    # Labeling
    plt.title('Total Gamma Results by Strike')
    plt.xlabel('Strike')
    plt.ylabel('Total Gamma')
    plt.xticks(strikes, [str(s) for s in strikes])  # Add a label on x-axis for each datapoint
    plt.tight_layout()

    plt.show()
    
ticker = 'SPY'
num_of_strikes = 5

gamma_results = compute_GEX(ticker, num_of_strikes)

print('GEX at each strike:')
for strike, gamma in gamma_results.items():
    print(f"Strike ({strike})")
    print(f"\tTotal: {int(gamma['Total'])}")
    print(f"\t\tC: {int(gamma['C'])}")
    print(f"\t\tP: {int(gamma['P'])}")

plot_gamma_results(gamma_results)
    