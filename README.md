# Trading Pipeline Application

This trading pipeline application is designed to perform real-time data streaming, process tick data, and execute trades based on Bollinger Bands and Rejection candlestick patterns. It uses the Deriv API for connecting to the market, fetching tick data, and placing trades on the selected symbol.
## Features

* Live Data Streaming: Connects to the Deriv WebSocket API to fetch tick data in real time.
* Technical Analysis: Uses Bollinger Bands and RSI to analyze market conditions and identify buy/sell signals.
* Automated Trading: Automatically executes trades when the appropriate signal is generated.
* Data Preprocessing: Processes live data to generate OHLC (Open, High, Low, Close) candlesticks from tick data.

### __Prerequisites__

Ensure that you have the following before running the application:

    Python 3.8+
    Pip for managing dependencies.
    Deriv API app ID and token. You can register for these at Deriv.

### __Setup__
__Step 1: Clone the Repository__

    git clone https://github.com/stephen-njiu/Trading-Pipeline
    cd <your-repo-directory>

__Step 2: Install the Requirements__

You can install the required dependencies using the requirements.txt file: <br>
    
    pip install -r requirements.txt


__Step 3: Set Up Your Environment__ <br>

* <i>You will need to provide your app ID and API token in the code:</i>

        app_id = '<your_app_id>'
        api_token = '<your_api_token>'

## __Running the Application__ <br>

__Step 1: Connect to the Market__

<i>The application connects to the Deriv WebSocket and streams tick data in real time. The first connection is established in the connect() function:</i>

    api = asyncio.run(connect())

__Step 2: Data Preprocessing and Candlestick Generation__

<i>Tick data is processed and converted into candlestick data using the create_candle() function. The data_preprocess() function applies Bollinger Bands, RSI, and Rejection candlestick patterns to the data:</i>

    df = data_preprocess(df)

__Step 3: Trading Logic__

<i>The trading strategy is based on Bollinger Bands and Rejection patterns. It triggers a buy or sell based on the signal generated:</i>

    Signal 1: Sell when the close and open prices are above the upper Bollinger Band.
    Signal 2: Buy when the close and open prices are below the lower Bollinger Band.

<i>The application places a trade using the api.proposal() and api.buy() functions once a signal is detected.

__Usage Example__</i>

__To run the application, execute the following command:__

    python main.py

* Once the application is running, it will stream tick data, process it into candlestick format, and execute trades based on the predefined strategy.

## Key Components

* WebSocket Connection: The application connects to Deriv’s WebSocket using websockets.connect().
* Tick Data Handling: Tick data is fetched and stored in the ticks list, which is later used to create candlesticks.
* Bollinger Bands & RSI: These are used to detect overbought or oversold conditions.
* Trade Execution: Trades are placed when the appropriate conditions are met.

### Customization

* Timeframe: You can change the candlestick timeframe by modifying the candle_stick_timeframe variable.
* Symbol: To trade on a different asset, replace the value of the tick_symbol variable.
* Trade Amount: Adjust the amount variable to set the stake for each trade.

### __License__

This project is open-source under the MIT License.

