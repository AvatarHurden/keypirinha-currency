from datetime import datetime
from enum import Enum
from .webservice import OpenExchangeRates, PrivateDomain

import json
import os
import re


class CurrencyError(RuntimeError):
    def __init__(self, currency):
        self.currency = currency

    def __str__(self):
        return 'Unrecognized currency "{}". You can create aliases in the package configuration file.'.format(self.currency)


class UpdateFreq(Enum):
    NEVER = 'never'
    HOURLY = 'hourly'
    DAILY = 'daily'


class ExchangeRates():

    _file_path = None
    last_update = None
    update_freq = None
    _currencies = {}
    _aliases = {}

    in_cur_fallback = 'USD'
    out_cur_fallback = 'EUR GBP'

    default_cur_in = 'USD'
    default_curs_out = ['EUR', 'GBP']

    error = None

    def __init__(self, path, update_freq, plugin):
        self.plugin = plugin
        self.cheap_service = PrivateDomain(self.plugin)
        self.expensive_service = OpenExchangeRates(self.plugin)
        self.update_freq = update_freq
        self._file_path = os.path.join(path, 'rates.json')

        if os.path.exists(self._file_path):
            try:
                self.load_from_file()
            except Exception as e:
                self.update()
        else:
            self.update()

        self.tryUpdate()

    def shouldUpdate(self):
        time_diff = datetime.now() - self.last_update
        if self.update_freq.value == UpdateFreq.HOURLY.value:
            return time_diff.total_seconds() >= 3600
        elif self.update_freq.value == UpdateFreq.DAILY.value:
            return time_diff.days >= 1
        else:
            return False

    def tryUpdate(self):
        if not self.last_update:
            return True
        if self.shouldUpdate():
            return self.update()
        else:
            return False

    def update(self):
        try:
            try:
                self._currencies, update_time = self.cheap_service.load_from_url()
                self.last_update = datetime.now()
                time_diff = self.last_update - datetime.fromtimestamp(update_time)

                if (time_diff.total_seconds() > 3600 * 2):
                    self.plugin.info('cache server is more than 2 hours old. Requesting from main API')
                    self._currencies, update_time = self.expensive_service.load_from_url()
            except Exception as e:
                self.plugin.info('cache server has returned error. Requesting from main API')
                self._currencies, update_time = self.expensive_service.load_from_url()

            self.save_to_file()
            self.error = None
            return True
        except Exception as e:
            self.error = e
            return False

    def load_from_file(self):
        with open(self._file_path) as f:
            data = json.load(f)

        self.last_update = datetime.strptime(data['last_update'], '%Y-%m-%dT%H:%M:%S')
        self._currencies = data['rates']
        self._load_secondary_data()

    def _load_secondary_data(self):
        pass

    def save_to_file(self):
        data = {
            'rates': self._currencies,
            'last_update': self.last_update.strftime('%Y-%m-%dT%H:%M:%S')
        }

        with open(self._file_path, 'w') as f:
            json.dump(data, f)

    def rate(self, code):
        if code == 'USD':
            return 1
        else:
            if code in self._aliases:
                return self.rate(self._aliases[code])
            else:
                return self._currencies[code]['price']

    def name(self, code):
        if code in self._aliases:
            return self.name(self._aliases[code])
        else:
            return self._currencies[code]['name']

    def format_codes(self, codeString):
        lst = [x.strip() for x in codeString.split(',')]
        return lst

    def clear_aliases(self):
        self._aliases.clear()

    def validate_alias(self, alias):
        validated = alias.upper()
        if len(validated) < 1:
            return None
        elif validated in self._currencies:
            return None
        elif validated in self._aliases:
            return None
        elif re.search('\d', validated):
            return None
        else:
            return validated

    def add_alias(self, alias, forCurrency):
        validatedCurrency = self.validate_code(forCurrency)
        self._aliases[alias] = validatedCurrency

    def validate_code(self, codeString, raiseOnNone=False):
        if codeString is None:
            if raiseOnNone:
                raise CurrencyError(None)
            return self.default_cur_in
        elif codeString.upper() in self._currencies or codeString.upper() in self._aliases:
            return codeString.upper()
        else:
            raise CurrencyError(codeString)

    def format_number(self, number, fullDigits=False):
        if fullDigits:
            formatted = '{:,.8f}'.format(number).rstrip('0').rstrip('.')
        else:
            formatted = '{:,.2f}'.format(number).rstrip('.')
        return formatted

    def convert(self, query):
        results = []
        for destination in query['destinations']:
            destinationCode = self.validate_code(destination['currency'], True)
            total = 0
            srcDescription = ''
            for index, source in enumerate(query['sources']):
                sourceCode = self.validate_code(source['currency'])
                rate = self.rate(destinationCode) / self.rate(sourceCode)
                amount = source['amount'] if source['amount'] else 1
                convertedAmount = rate * amount
                total += convertedAmount
                if amount < 0 or index > 0:
                    srcDescription += ' - ' if amount < 0 else ' + '
                srcDescription += '{} {}'.format(self.format_number(abs(amount)),
                                                 self.name(sourceCode))

            fullDigits = len(query['sources']) == 1 and \
                (query['sources'][0]['amount'] or 1) == 1

            formatted_total = self.format_number(total, fullDigits)
            result = {
                'amount': total,
                'description': srcDescription,
                'title': '{}'.format(formatted_total + ' ' + self.name(destinationCode))
            }
            results.append(result)
        return results

    def set_default_cur_in(self, string):
        code = string.upper()
        if code in self._currencies.keys():
            self.default_cur_in = code
            return True
        else:
            return False

    def set_default_curs_out(self, string):
        lst = string.split()
        curs = [x.upper() for x in lst if x.upper() in self._currencies.keys()]
        if len(lst) != len(curs):
            return False
        self.default_curs_out = curs
        return True
