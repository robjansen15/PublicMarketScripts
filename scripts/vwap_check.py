import requests
from datetime import datetime, timedelta

###READ ME###
# Depends on polygon options
# https://polygon.io

def get_api_key_from_file(filename='polygon-key.txt'):
    try:
        with open(filename, 'r') as f:
            # Read the first line of the file, which is expected to be the API key
            api_key = f.readline().strip()
        return api_key
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def get_contract_for_date(date, strike_price, contract_type="call", api_key=""):
    params = {
        "expiration_date": date,
        "contract_type": contract_type,
        "strike_price": strike_price,
        "apiKey": api_key
    }
    
    response = requests.get(API_URL, params=params)
    
    if response.status_code != 200:
        print(f"Failed to fetch data for date {date}. Status code: {response.status_code}")
        return None
    
    data = response.json()
    if 'results' not in data or len(data['results']) == 0:
        return None

    return data['results'][0]

def compute_vwap(date, strike_price, contract_type="call", api_key=""):
    contract = get_contract_for_date(date, strike_price, contract_type, api_key)
    if not contract:
        return False

    return contract['day']['close'] < contract['day']['vwap'], contract['day']['close'], contract['day']['vwap']

# Assuming you want to check for a specific contract on a given date:
specific_date = "2023-09-15"
specific_strike_price = 175
option_type = "call"
ticker = "AAPL"

API_URL = f"https://api.polygon.io/v3/snapshot/options/{ticker}"
api_key = get_api_key_from_file()

is_price_less_than_vwap, price, vwap = compute_vwap(specific_date, specific_strike_price, option_type, api_key)

if is_price_less_than_vwap:
    print(f"Less than the VWAP. price ({price}), vwap ({vwap})")
else:
    print(f"More than the VWAP. price ({price}), vwap ({vwap})")