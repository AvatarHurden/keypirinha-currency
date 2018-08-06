import keypirinha_net as kpnet
import urllib
import json


class YahooFinance():

    url = "http://finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote?format=json"

    def load_from_url(self):
        print("loading from url...")
        opener = kpnet.build_urllib_opener()
        opener.addheaders = [("User-agent", "Mozilla/5.0")]
        with opener.open(self.url) as conn:
            response = conn.read()
        data = json.loads(response)
        rates = data['list']['resources']

        currencies = {}
        for rate in rates:
            try:
                fields = rate['resource']['fields']
                symbol = fields['symbol'][0:3]
                name = fields['name'].replace('USD/', '')
                price = float(fields['price'])

                private_rate = {
                    'name': name,
                    'price': price
                }

                currencies[symbol] = private_rate
            except Exception:
                pass

        return currencies

    def _load_secondary_data(self):
        pass


class OpenExchangeRates():

    url = 'https://openexchangerates.org/api/latest.json'
    APPID = '462d6b7ade734ce1b59201196765d8d7'

    def build_request(self, parameters):
        return self.url + '?' + urllib.parse.urlencode(parameters)

    def load_from_url(self):
        print("loading from url...")
        opener = kpnet.build_urllib_opener()
        opener.addheaders = [("User-agent", "Mozilla/5.0")]

        params = {'app_id': self.APPID,
                  'show_alternative': True}

        requestURL = self.build_request(params)

        with opener.open(requestURL) as conn:
            response = conn.read()
        data = json.loads(response)
        rates = data['rates']

        currencies = {}
        for rate in rates:
            private_rate = {
                'name': rate,
                'price': rates[rate]
            }

            currencies[rate] = private_rate

        return currencies
