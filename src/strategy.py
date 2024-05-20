import random
import backtrader as bt


class SwingStrategy(bt.Strategy):

    def __init__(
        self,
        rsi_period=14,
        rsi_upper=70,
        rsi_lower=30,
        trail_perc=0.05,
        reverse=True,
        backtesting=False,
    ):
        self.params.rsi_period = rsi_period
        self.params.rsi_upper = rsi_upper
        self.params.rsi_lower = rsi_lower
        self.params.trail_perc = trail_perc
        self.params.reverse = reverse
        self.params.backtesting = backtesting
        self.rsi = {
            data: bt.indicators.RSI(data, period=self.params.rsi_period)
            for data in self.datas
        }
        self.order_reasons = {}
        self.orders = {data: None for data in self.datas}
        self.trail_orders = {data: [] for data in self.datas}

    def log(self, txt):
        if not self.params.backtesting:
            print(f"{self.datas[0].datetime.date(0)} - {txt}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY {order.data._name}, Price: {order.executed.price}, Size: {order.executed.size}"
                )
            elif order.issell():
                reason = self.order_reasons.get(order.ref, "Unknown Reason")
                self.log(
                    f"SELL {order.data._name}, Price: {order.executed.price}, Size: {order.executed.size} due to {reason}"
                )
                if order.ref in self.order_reasons:  # Clean up after using the reason
                    del self.order_reasons[order.ref]

    def next(self):
        # Step 1: Sell if RSI > self.params.rsi_upper
        positions = self.getpositions()
        for data, pos in positions.items():
            if self.orders[data] and self.orders[data].status in [
                bt.Order.Completed,
                bt.Order.Canceled,
                bt.Order.Expired,
            ]:
                self.orders[data] = None
            if self.trail_orders[data]:
                new_trail_orders = []
                for trail_order in self.trail_orders[data]:
                    if trail_order.status in [
                        bt.Order.Completed,
                        bt.Order.Canceled,
                        bt.Order.Expired,
                    ]:
                        continue
                    new_trail_orders.append(trail_order)
                self.trail_orders[data] = new_trail_orders

            if pos.size:  # Position is open
                if self.rsi[data] > self.params.rsi_upper:  # Positions should be closed
                    # Cancel all trailing stop orders
                    for trail_order in self.trail_orders[data]:
                        self.cancel(trail_order)
                    self.trail_orders[data] = []

                    self.orders[data] = self.close(data)
                    self.order_reasons[self.orders[data].ref] = "RSI Signal"

        # Step 2: Buy if RSI < self.params.rsi_lower
        eligible_stocks = [
            data for data in self.datas if self.rsi[data] < self.params.rsi_lower
        ]
        if not eligible_stocks:
            return  # No buying opportunity

        if self.params.reverse is None:
            random.shuffle(eligible_stocks)
        else:
            eligible_stocks.sort(
                key=lambda data: data.close[0], reverse=self.params.reverse
            )

        cash = self.broker.get_cash()
        num_affordable_stocks = len(eligible_stocks)
        affordable_stocks = []

        # Dynamically adjust the budget per stock
        for data in eligible_stocks:
            budget_per_stock = cash / num_affordable_stocks
            if data.close[0] <= budget_per_stock:  # affordable
                affordable_stocks.append(data)
            else:  # not affordable
                num_affordable_stocks -= 1

        # Execute buy orders for affordable stocks
        for data in affordable_stocks:
            budget_per_stock = cash / len(affordable_stocks)
            size = int(budget_per_stock / data.close[0])
            if size > 0:
                self.log(f"Buying {size} shares of {data._name} at {data.close[0]}")
                self.orders[data] = self.buy(data, size=size)
                trail_order = self.sell(
                    data,
                    size=size,
                    exectype=bt.Order.StopTrail,
                    trailpercent=self.params.trail_perc,
                )
                self.trail_orders[data].append(trail_order)
                self.order_reasons[trail_order.ref] = "Trailing Stop"

    def stop(self):
        print(
            f"{self.datas[0].datetime.date(0)} - Final Portfolio Value: ${self.broker.getvalue():.2f}"
        )
        open_positions = [data for data in self.datas if self.getposition(data).size]
        if open_positions:
            self.log(
                f'Open positions: {", ".join([data._name for data in open_positions])}'
            )
        else:
            self.log("No open positions")
