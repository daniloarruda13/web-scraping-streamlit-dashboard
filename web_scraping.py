import requests
from urllib.parse import unquote
from datetime import datetime
import pytz
import pandas as pd



def fetch_barchart_data():
    # Fields to be fetched from the database
    fields = ['symbol', 'baseSymbol', 'expirationDate', 'strikePrice', 'moneyness', 'bidPrice', 'midpoint',
              'askPrice', 'lastPrice', 'priceChange', 'percentChange', 'volume',
              'openInterest', 'openInterestChange', 'delta', 'volatility', 'optionType',
              'daysToExpiration', 'tradeTime', 'averageVolatility',
              'historicVolatility30d', 'baseNextEarningsDate', 'dividendExDate', 'symbolCode',
              'symbolType']

    # Establishing a session to retrieve cookies (authorization)
    with requests.Session() as s:
        start_url = 'https://www.barchart.com/'
        start_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
        start = s.get(start_url, headers=start_headers)
        cookie_dict = s.cookies.get_dict()
        cookie_str = '; '.join([x + "=" + y for x, y in cookie_dict.items()])
        cookie_str += "; bcFreeUserPageView=0;"
        xsrf_token = unquote(cookie_dict['XSRF-TOKEN'])

        # Creating headers for the database request
        headers = {
            'Accept': '*/*',
            'Cookie': cookie_str,
            'Referer': 'https://www.barchart.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'X-Xsrf-Token': xsrf_token
        }

        # Retrieving the expiration dates for monthly and weekly options
        initial_table = 'https://www.barchart.com/proxies/core-api/v1/options-expirations/get?fields=expirationDate%2CexpirationType%2CdaysToExpiration%2CputVolume%2CcallVolume%2CputCallVolumeRatio%2CputOpenInterest%2CcallOpenInterest%2CputCallOpenInterestRatio%2CaverageVolatility%2CsymbolCode%2CsymbolType%2ClastPrice%2CdailyLastPrice&symbol=%24VIX&meta=field.shortName%2Cfield.type%2Cfield.description&page=1&limit=100&raw=1'
        response = s.get(initial_table, headers=headers)
        data = response.json()

        monthly_dates = set()
        weekly_dates = set()

        for item in data['data']:
            expiration_date = item['expirationDate']
            expiration_type = item['expirationType']

            if expiration_type == 'monthly':
                monthly_dates.add(expiration_date)
            elif expiration_type == 'weekly':
                weekly_dates.add(expiration_date)

        dates_urls = {'Monthly': [], 'Weekly': []}

        def database_url(baseSymbol, fields, expirationDate, orderBy, expirationType):
            base_url = 'https://www.barchart.com/proxies/core-api/v1/options/get'
            requested_fields = '%2C'.join(fields)
            link = f'{base_url}?baseSymbol={baseSymbol}&fields={requested_fields}&groupBy=optionType&expirationDate={expirationDate}&meta=field.shortName%2Cexpirations%2Cfield.description&orderBy={orderBy}&orderDir=asc&optionsOverview=true&expirationType={expirationType}&raw=1'
            return link

        for date in monthly_dates:
            date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
            dates_urls['Monthly'].append(database_url('$VIX', fields, date, 'strikePrice', 'monthly'))

        for date in weekly_dates:
            date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
            dates_urls['Weekly'].append(database_url('$VIX', fields, date, 'strikePrice', 'weekly'))

        def fetch_data(urls, option_type):
            option_data = []
            for url in urls:
                response = s.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    option = data.get('data', {}).get(option_type)
                    if option:
                        option_data.extend(option)
            return option_data

        call_monthly_df = pd.DataFrame(fetch_data(dates_urls['Monthly'], 'Call')).drop('raw', axis=1)
        put_monthly_df = pd.DataFrame(fetch_data(dates_urls['Monthly'], 'Put')).drop('raw', axis=1)
        call_weekly_df = pd.DataFrame(fetch_data(dates_urls['Weekly'], 'Call')).drop('raw', axis=1)
        put_weekly_df = pd.DataFrame(fetch_data(dates_urls['Weekly'], 'Put')).drop('raw', axis=1)

        current_time = datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S %Z%z')

        call_monthly_df['time'] = current_time
        put_monthly_df['time'] = current_time
        call_weekly_df['time'] = current_time
        put_weekly_df['time'] = current_time

        monthly_vix = pd.concat([call_monthly_df, put_monthly_df])
        weekly_vix = pd.concat([call_weekly_df, put_weekly_df])

        return monthly_vix, weekly_vix


def update_datasets():
    monthly_vix, weekly_vix = fetch_barchart_data()

    monthly_vix_file_name = 'monthly_vix.csv'
    weekly_vix_file_name = 'weekly_vix.csv'

    # Assuming you want to save to CSV files locally
    monthly_vix.to_csv(monthly_vix_file_name, index=False)
    weekly_vix.to_csv(weekly_vix_file_name, index=False)

    print("Monthly dataset has been updated and saved to 'monthly_vix.csv'")
    print("Weekly dataset has been updated and saved to 'weekly_vix.csv'")


# Running the update function when the script is executed
if __name__ == "__main__":
    update_datasets()
