using System;
using System.Linq;
using System.Collections.Generic;
using HtmlAgilityPack;

namespace CSharpwebscraper
{
    public class Webscraper
    {
        // there is information we can fetch once that we don't need to get again
        public List<string> Initial(String[] stock_tickers)
        {
            HtmlWeb web = new HtmlWeb();
            var Initial_Stock_info = new List<string> { };
            for (int i = 0; i < stock_tickers.Length; i++)
            {
                String ticker = stock_tickers[i];
                String url = "https://finance.yahoo.com/quote/" + ticker + "?p=" + ticker;
                HtmlDocument doc = web.Load(url);
                Initial_Stock_info.Add(ticker);

                var Yield = doc.DocumentNode.SelectNodes("//td[@data-test='DIVIDEND_AND_YIELD-value']").ToList();
                foreach (var item in Yield)
                {
                    string dividend = item.InnerText;
                    String consoleoutput = ticker + " Stock Dividend/Yield: " + dividend;
                    Console.WriteLine(consoleoutput);
                    Initial_Stock_info.Add(dividend);
                }
                var DaysRange = doc.DocumentNode.SelectNodes("//td[@data-test='DAYS_RANGE-value']").ToList();
                foreach (var item in DaysRange)
                {
                    string range = item.InnerText;
                    String consoleoutput = ticker + " Days High and Low Range: " + range;
                    Console.WriteLine(consoleoutput);
                    Initial_Stock_info.Add(range);
                }
                var Fifty_Two_WeekRange = doc.DocumentNode.SelectNodes("//td[@data-test='FIFTY_TWO_WK_RANGE-value']").ToList();
                foreach (var item in Fifty_Two_WeekRange)
                {
                    string yearrange = item.InnerText;
                    String consoleoutput = ticker + " Yearly High and Low Range: " + yearrange;
                    Console.WriteLine(consoleoutput);
                    Initial_Stock_info.Add(yearrange);
                }
                var Previous_Close = doc.DocumentNode.SelectNodes("//td[@data-test='PREV_CLOSE-value']").ToList();
                foreach (var item in Previous_Close)
                {
                    string prev_price = item.InnerText;
                    String consoleoutput = ticker + " Stock Previous Close Price: " + prev_price;
                    Console.WriteLine(consoleoutput);
                    Initial_Stock_info.Add(prev_price);
                }
                var Open = doc.DocumentNode.SelectNodes("//td[@data-test='OPEN-value']").ToList();
                foreach (var item in Open)
                {
                    string open_price = item.InnerText;
                    String consoleoutput = ticker + " Stock Open Price: " + open_price;
                    Console.WriteLine(consoleoutput);
                    Initial_Stock_info.Add(open_price);
                }
                var PE = doc.DocumentNode.SelectNodes("//td[@data-test='PE_RATIO-value']").ToList();
                foreach (var item in PE)
                {
                    string pe_ratio = item.InnerText;
                    String consoleoutput = ticker + " Price to Earnings: " + pe_ratio;
                    Console.WriteLine(consoleoutput);
                    Initial_Stock_info.Add(pe_ratio);
                }
                var Average_Volume = doc.DocumentNode.SelectNodes("//td[@data-test='AVERAGE_VOLUME_3MONTH-value']").ToList();
                foreach (var item in Average_Volume)
                {
                    string avg_volume = item.InnerText;
                    String consoleoutput = ticker + " Average 3-month Volume: " + avg_volume;
                    Console.WriteLine(consoleoutput);
                    Initial_Stock_info.Add(avg_volume);
                }
                var One_Year_Target = doc.DocumentNode.SelectNodes("//td[@data-test='ONE_YEAR_TARGET_PRICE-value']").ToList();
                foreach (var item in One_Year_Target)
                {
                    string target = item.InnerText;
                    String consoleoutput = ticker + " One year Price Target: " + target;
                    Console.WriteLine(consoleoutput);
                    Initial_Stock_info.Add(target);
                }
                var Beta = doc.DocumentNode.SelectNodes("//td[@data-test='BETA_5Y-value']").ToList();
                foreach (var item in Beta)
                {
                    string beta = item.InnerText;
                    String consoleoutput = ticker + " Beta (Correlation with market): " + beta;
                    Console.WriteLine(consoleoutput);
                    Initial_Stock_info.Add(beta);
                }
            }
            return Initial_Stock_info;
        }
        public List<string> Scraper(String[] stock_tickers)
        {
            HtmlWeb web = new HtmlWeb();
            var Stock_Info = new List<string> { };
            for (int i = 0; i < stock_tickers.Length; i++)
            {
                String ticker = stock_tickers[i];
                String url = "https://finance.yahoo.com/quote/" + ticker + "?p=" + ticker;
                HtmlDocument doc = web.Load(url);
                Stock_Info.Add(ticker);
                var Quote = doc.DocumentNode.SelectNodes("//fin-streamer[@class='Fw(b) Fz(36px) Mb(-4px) D(ib)']").ToList();
                foreach (var item in Quote)
                {
                    string price = item.InnerText;
                    String consoleoutput = ticker + " Stock Price: " + price;
                    Console.WriteLine(consoleoutput);
                    Stock_Info.Add(price);
                }
                var Indicator = doc.DocumentNode.SelectNodes("//div[@class='Fz(xs) Mb(4px)']").ToList();
                foreach (var item in Indicator)
                {
                    string indicator = item.InnerText;
                    int index = indicator.IndexOf("p");
                    if (index > 0)
                        indicator = indicator.Substring(0, index);
                    String consoleoutput = ticker + " Stock Indicator: " + indicator;
                    Console.WriteLine(consoleoutput);
                    Stock_Info.Add(indicator);
                }
                var Volume = doc.DocumentNode.SelectNodes("//td[@data-test='TD_VOLUME-value']").ToList();
                foreach (var item in Volume)
                {
                    string volume = item.InnerText;
                    String consoleoutput = ticker + " Stock Volume: " + volume;
                    Console.WriteLine(consoleoutput);
                    Stock_Info.Add(volume);
                }
                var Bid = doc.DocumentNode.SelectNodes("//td[@data-test='BID-value']").ToList();
                foreach (var item in Bid)
                {
                    string bid = item.InnerText;
                    String consoleoutput = ticker + " Stock Bids: " + bid;
                    Console.WriteLine(consoleoutput);
                    Stock_Info.Add(bid);
                }
                var Ask = doc.DocumentNode.SelectNodes("//td[@data-test='ASK-value']").ToList();
                foreach (var item in Ask)
                {
                    string ask = item.InnerText;
                    String consoleoutput = ticker + " Stock Asks: " + ask;
                    Console.WriteLine(consoleoutput);
                    Stock_Info.Add(ask);
                }
            }
            return Stock_Info;
        }
    }
}
