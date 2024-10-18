# get the imports
from deriv_api import DerivAPI
from deriv_api import APIError
import asyncio
import nest_asyncio
import pandas as pd
import numpy as np
import ta
import time
import websockets
import time
from datetime import datetime, timedelta
nest_asyncio.apply()

#constants
app_id = ''
api_token = ''
candle_stick_timeframe = 60 # as seconds
interval_min = int(candle_stick_timeframe/60)
prediction_candles = 3
duration = int(candle_stick_timeframe * prediction_candles)
amount = 100
tick_symbol = '1HZ10V'
count = 5000
data_dict ={
  "ticks_history":tick_symbol,
  "adjust_start_time": 1,
  "count": count,
  "end": "latest",
  "granularity":candle_stick_timeframe,
  "style": "candles"
}
subscription_id = 0

def data_preprocess(df):
    # pass a dataframe and determine whether a signal has been generated or not...
    period = 20
    df['moving_avg'] = df['close'].rolling(window=period).mean()
    df['std_dev'] = df['close'].rolling(window=period).std()
    df['upper_bollinger'] = df['moving_avg'] + (df['std_dev'] * 2)
    df['lower_bollinger'] = df['moving_avg'] - (df['std_dev'] * 2)
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df.dropna(inplace = True)
    # check if the closing and open price are both above bbtop(1) or are below bblower(2) else 0
    df['check_candle']= np.where((df['close'] > df['upper_bollinger']) & (df['open'] > df['upper_bollinger']),1,
                                np.where((df['close'] < df['lower_bollinger']) & (df['open'] < df['lower_bollinger']),2,0))
    df['candle_pos'] = np.where((df['check_candle'] == 1) & (df['rsi'] >= 70), 1,
                                np.where((df['check_candle'] == 2) & (df['rsi'] <= 30), 2, 0))
    ## Adding the Rejection candlestick pattern 
    body_size = abs(df['close'] - df['open'])
    lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
    upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)

    # Conditions for bullish rejection (long lower shadow) and bearish rejection (long upper shadow)
    bullish_rejection = (lower_shadow >= 1.8 * body_size) & (upper_shadow <= lower_shadow / 2).astype(int)
    bearish_rejection = (upper_shadow >= 1.8 * body_size) & (lower_shadow <= upper_shadow / 2).astype(int)
    df['signal'] = np.where(((df['candle_pos'] == 1) & (bearish_rejection == 1)), 1,
                                 np.where(((df['candle_pos'] == 2) & (bullish_rejection == 1)),2,0))
    return df

async def connect():
    # global api
    global author
    try:
        # Attempt to reconnect and reauthorize
        connection = await websockets.connect(f'wss://ws.derivws.com/websockets/v3?app_id={app_id}')
        api = DerivAPI(connection=connection)
        author = await api.authorize(api_token)
        print("Reconnected and authorized.")
    except Exception as e:
        print(f"Failed to reconnect: {e}")
        await connect()  # Retry reconnection if it fails
    return api
api = asyncio.run(connect())

balance = author['authorize']['balance']
# print(balance)
amount = round(0.05 * balance,1)

async def sample_calls():
    data = await api.ticks_history(data_dict)
    data = data['candles']
    df = pd.DataFrame(data)
    del df['epoch']
    df = df[:-1] # since trading will start at the next [single_row] download data interval
    return df

async def get_barrier():
    try:
        # Requesting contract details for 'R_10'
        response = await api.contracts_for({
            'contracts_for': tick_symbol,  # Symbol for R_10
            'currency': 'USD'        # Specify currency
        })
        
        # Check and return the contract details
        if 'contracts_for' in response:
            bar =  response['contracts_for']['available'][54]['barrier']
            return bar
        else:
            return f"Error: {response.get('error', 'Unable to fetch contract details')}"
    
    except APIError as e:
        return f"APIError: {e}"

# Call the function to fetch contract details for the tick_symbol

import time
def create_candle(ticks):
    if ticks:
        # Open, Close, High, Low calculations
        open_price = ticks[1]
        close_price = ticks[-2]
        high_price = max(ticks)
        low_price = min(ticks)
        
        # Candle (OHLC) data
        candle = {
            "open": open_price,
            "close": close_price,
            "high": high_price,
            "low": low_price,
            "timestamp": datetime.now()
        }
        return candle
    return None

import asyncio
from functools import partial
df = None
df2 = None
ticks = []
all_candles = []
current_minute = datetime.now().minute
loop = asyncio.get_event_loop()

async def tick_50_callback(data):
    global current_minute, ticks, all_candles, bar, df
    global df2
    bar = await get_barrier()  
    current_price = data['tick']['quote']
    now = datetime.now()   
    ticks.append(current_price)   
    if now.minute != current_minute:
        candle = create_candle(ticks)
        if len(all_candles) == 1:
            df = asyncio.run(sample_calls())
            print(len(df))
        elif len(all_candles) > 1:
            candle.popitem()
            dict1 = pd.DataFrame([candle])
            df = pd.concat([df, dict1], ignore_index = True)
            df2 = data_preprocess(df)
            if len(df2) > 2:
                if df2.iloc[-1].signal == 1:

                    proposal = await api.proposal({"proposal": 1, "amount":amount , "barrier": bar, "basis": "stake",
                                       "contract_type": "ONETOUCH", "currency": "USD", "duration": duration, "duration_unit": "s",
                                       "symbol": tick_symbol})
                    price = proposal['proposal']['ask_price']
                    proposal_id = proposal.get('proposal').get('id')
                    await api.buy({"buy": proposal_id, "price": price})
                    # open a sell trade
                    pass
                elif df2.iloc[-1].signal == 2:
                    proposal = await api.proposal({"proposal": 1, "amount":amount , "barrier": bar, "basis": "stake",
                                       "contract_type": "ONETOUCH", "currency": "USD", "duration": duration, "duration_unit": "s",
                                       "symbol": tick_symbol})
                    price = proposal['proposal']['ask_price']
                    proposal_id = proposal.get('proposal').get('id')
                    await api.buy({"buy": proposal_id, "price": price})
                    # open a buy trade
                    
                else:
                    print('No Signal')
                # if signal is produced open a trade...
        # if len(all_candles) > 3:
        #     print(all_candles)
        #     all_candles.pop(0)
        #     df = df.drop(index=0).reset_index(drop=True)
        # print(len(all_candles))
        if candle:
            print(f"1 Minute Candle: {candle}")
        ticks.clear()
        current_minute = now.minute
    
    print(f"Current price: {current_price} | len of all_candles {len(all_candles)}")

def sync_callback(data):
    asyncio.create_task(tick_50_callback(data))
    # Alternative if you're not in an async context:
    # loop.create_task(tick_50_callback(data))

dir

async def run_program():       
    # Subscribe using the synchronous wrapper
    source_tick_50 = await api.subscribe({'ticks': tick_symbol})
    source_tick_50.subscribe(sync_callback)

asyncio.run(run_program())