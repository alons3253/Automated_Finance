using System;
using System.Threading.Tasks;
using Alpaca.Markets;

namespace CSharpTradeExecutor
{
    public class BracketOrders
    {
        public static async Task Trader(string[] array)
        {
            String symbol = "";
            String side = "";
            int round_lot = 0;
            decimal stopLossStopPrice = 1.0m;
            decimal takeProfitLimitPrice = 1.0m;
            decimal stopLossLimitPrice = 1.0m;

            for (int i = 0; i < array.Length; i++)
            {
                if (i == 0)
                {
                    symbol = array[i];
                }
                else if (i == 1)
                {
                    side = array[i];
                }
                else if (i == 2)
                {
                    round_lot = int.Parse(array[i]);
                }
                else if (i == 3)
                {
                    stopLossStopPrice = decimal.Parse(array[i]);
                }
                else if (i == 4)
                {
                    takeProfitLimitPrice = decimal.Parse(array[i]);
                }
                else if (i == 5)
                {
                    stopLossLimitPrice = decimal.Parse(array[i]);
                }
            }

            var tradingClient = Alpaca.Markets.Environments.Paper.GetAlpacaTradingClient(
                                new SecretKey("PKCPC6RJ84BG84W3PB60", "U1r9Z2QknL9FwAaTztfLl5g1DTxpa5m97qyWCGZ7"));

            if (side == "buy")
            {
                await tradingClient.PostOrderAsync(MarketOrder.Buy(symbol, round_lot).WithDuration(TimeInForce.Gtc).
                                    Bracket(stopLossStopPrice: stopLossStopPrice, takeProfitLimitPrice: takeProfitLimitPrice,
                                    stopLossLimitPrice: stopLossLimitPrice));
            }
            if (side == "sell")
            {
                await tradingClient.PostOrderAsync(MarketOrder.Sell(symbol, round_lot).WithDuration(TimeInForce.Gtc).
                                    Bracket(stopLossStopPrice: stopLossStopPrice, takeProfitLimitPrice: takeProfitLimitPrice,
                                    stopLossLimitPrice: stopLossLimitPrice));
            }
        }
    }
}
