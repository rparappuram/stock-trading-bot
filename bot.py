from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from config import API_KEY, SECRET_KEY

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# search for crypto assets
search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)

assets = trading_client.get_all_assets(search_params)

# preparing orders
market_order_data = MarketOrderRequest(
                    symbol="SPY",
                    qty=0.023,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                    )

# Market order
market_order = trading_client.submit_order(
                order_data=market_order_data
               )
print(f"Market order: \n{market_order}", end="\n\n")

# params to filter orders by
request_params = GetOrdersRequest(
                    status=QueryOrderStatus.OPEN,
                    side=OrderSide.SELL
                 )

# orders that satisfy params
orders = trading_client.get_orders(filter=request_params)
print(f"Orders: \n{orders}", end="\n\n")


# # get all positions
positions = trading_client.get_all_positions()
print(f"Positions: \n{positions}", end="\n\n")