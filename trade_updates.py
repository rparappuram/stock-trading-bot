from config import API_KEY, SECRET_KEY
from alpaca.trading.stream import TradingStream


trading_stream = TradingStream(API_KEY, SECRET_KEY, paper=True)

async def update_handler(data):
    # trade updates will arrive in our async handler
    print(data)

# subscribe to trade updates and supply the handler as a parameter
trading_stream.subscribe_trade_updates(update_handler)

# start our websocket streaming
trading_stream.run()