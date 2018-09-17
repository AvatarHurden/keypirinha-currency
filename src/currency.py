# Keypirinha launcher (keypirinha.com)

import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet

from .exchange import ExchangeRates, UpdateFreq

import re
import json
import traceback
import urllib.error
import urllib.parse
from html.parser import HTMLParser

class Currency(kp.Plugin):
    """
    One-line description of your plugin.

    This block is a longer and more detailed description of your plugin that may
    span on several lines, albeit not being required by the application.

    You may have several plugins defined in this module. It can be useful to
    logically separate the features of your package. All your plugin classes
    will be instantiated by Keypirinha as long as they are derived directly or
    indirectly from :py:class:`keypirinha.Plugin` (aliased ``kp.Plugin`` here).

    In case you want to have a base class for your plugins, you must prefix its
    name with an underscore (``_``) to indicate Keypirinha it is not meant to be
    instantiated directly.

    In rare cases, you may need an even more powerful way of telling Keypirinha
    what classes to instantiate: the ``__keypirinha_plugins__`` global variable
    may be declared in this module. It can be either an iterable of class
    objects derived from :py:class:`keypirinha.Plugin`; or, even more dynamic,
    it can be a callable that returns an iterable of class objects. Check out
    the ``StressTest`` example from the SDK for an example.

    Up to 100 plugins are supported per module.

    More detailed documentation at: http://keypirinha.com/api/plugin.html
    """
    API_URL = "http://query.yahooapis.com/v1/public/yql"
    API_USER_AGENT = "Mozilla/5.0"

    ITEMCAT_CONVERT = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_UPDATE = kp.ItemCategory.USER_BASE + 2
    ITEMCAT_RESULT = kp.ItemCategory.USER_BASE + 3

    DEFAULT_SECTION = 'defaults'

    DEFAULT_ITEM_ENABLED = True
    DEFAULT_UPDATE_FREQ = 'daily'
    DEFAULT_ALWAYS_EVALUATE = True
    DEFAULT_ITEM_LABEL = 'Convert Currency'
    DEFAULT_CUR_IN = 'USD'
    DEFAULT_CUR_OUT = 'EUR, GBP'

    default_item_enabled = DEFAULT_ITEM_ENABLED
    update_freq = UpdateFreq(DEFAULT_UPDATE_FREQ)
    always_evaluate = DEFAULT_ALWAYS_EVALUATE
    default_item_label = DEFAULT_ITEM_LABEL
    default_cur_in = DEFAULT_CUR_IN
    default_cur_out = DEFAULT_CUR_OUT

    ACTION_COPY_RESULT = 'copy_result'
    ACTION_COPY_AMOUNT = 'copy_amount'

    broker = None

    def __init__(self):
        super().__init__()

    def on_start(self):
        self._read_config()

        actions = [
            self.create_action(
                name=self.ACTION_COPY_AMOUNT,
                label="Copy result",
                short_desc="Copy the result to clipboard"),
            self.create_action(
                name=self.ACTION_COPY_RESULT,
                label="Copy result with code",
                short_desc="Copy result (with code) to clipboard")]

        self.set_actions(self.ITEMCAT_RESULT, actions)

    def on_catalog(self):
        catalog = []

        if self.default_item_enabled:
            catalog.append(self._create_translate_item(
                label=self.default_item_label))

        self.set_catalog(catalog)
        self._update_update_item()

    def on_suggest(self, user_input, items_chain):
        suggestions = []

        if items_chain and items_chain[-1].category() == self.ITEMCAT_RESULT:
            self.set_suggestions(items_chain, kp.Match.ANY, kp.Sort.NONE)
            return
        if not items_chain or items_chain[-1].category() != self.ITEMCAT_CONVERT:
            if not self.always_evaluate:
                return
            query = self._parse_and_merge_input(user_input, True)
            if 'from_cur' not in query and 'to_cur' not in query:
                return

        if self.should_terminate(0.25):
            return
        try:
            query = self._parse_and_merge_input(user_input)
            if not query['from_cur'] or not query['to_cur'] or not user_input:
                return

            if self.broker.tryUpdate():
                self._update_update_item()

            if self.broker.error:
                suggestions.append(self.create_error_item(
                    label=user_input,
                    short_desc="Webservice failed ({})".format(self.broker.error)))
            else:
                results = self.broker.convert(query['amount'], query['from_cur'], query['to_cur'])

                for result in results:
                    suggestions.append(self._create_result_item(
                        label=result['title'],
                        short_desc= result['source'] + ' to ' + result['destination'],
                        target=result['title']
                    ))
        except Exception as exc:
            suggestions.append(self.create_error_item(
                label=user_input,
                short_desc="Error: " + str(exc)))

        self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)
        # else
        #     suggestions = [self._create_keyword_item(
        #         label=user_input,
        #         short_desc="Convert values between currencies")]
        #     self.set_suggestions(suggestions)

    def on_execute(self, item, action):
        if item.category() == self.ITEMCAT_UPDATE:
            self.broker.update()
            self._update_update_item()
            return
        if item.category() != self.ITEMCAT_RESULT:
            return

        # browse or copy url
        if action and action.name() == self.ACTION_COPY_AMOUNT:
            amount = item.data_bag()[:-4]

            kpu.set_clipboard(amount)
        # default action: copy result (ACTION_COPY_RESULT)
        else:
            kpu.set_clipboard(item.data_bag())

    def on_activated(self):
        pass

    def on_deactivated(self):
        pass

    def on_events(self, flags):
        if flags & (kp.Events.APPCONFIG | kp.Events.PACKCONFIG |
                    kp.Events.NETOPTIONS):
            self._read_config()
            self.on_catalog()

    def _parse_and_merge_input(self, user_input=None, empty=False):
        if empty:
            query = {}
        else:
            query = {
                'from_cur': self.default_cur_in,
                'to_cur': self.default_cur_out,
                'amount': 1
            }

        # parse user input
        # * supported formats:
        #     <amount> [[from_cur][( to | in |:)to_cur]]
        if user_input:
            user_input = user_input.lstrip()
            query['terms'] = user_input.rstrip()

            symbolRegex = r'[a-zA-Z]{3}(,\s*[a-zA-Z]{3})*'

            m = re.match(
                (r"^(?P<amount>\d*([,.]\d+)?)?\s*" +
                    r"(?P<from_cur>" + symbolRegex + ")?\s*" +
                    r"(( to | in |:)\s*(?P<to_cur>" + symbolRegex +"))?$"),
                user_input)

            if m:
                if m.group('from_cur'):
                    from_cur = self.broker.validate_codes(m.group('from_cur'))
                    if from_cur:
                        query['from_cur'] = from_cur
                if m.group('to_cur'):
                    to_cur = self.broker.validate_codes(m.group('to_cur'))
                    if to_cur:
                        query['to_cur'] = to_cur
                if m.group('amount'):
                    query['amount'] = float(m.group('amount').rstrip().replace(',', '.'))
        return query

    def _update_update_item(self):
        self.merge_catalog([self.create_item(
            category=self.ITEMCAT_UPDATE,
            label='Update Currency',
            short_desc='Last updated at ' + self.broker.last_update.isoformat(),
            target="updatecurrency",
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE)])

    def _create_translate_item(self, label):

        def joinCur(lst):
            if len(lst) == 1:
                return lst[0]
            else:
                return ', '.join(lst[:-1]) + ' and ' + lst[-1]

        desc = 'Convert from {} to {}'.format(joinCur(self.default_cur_in), joinCur(self.default_cur_out))

        return self.create_item(
            category=self.ITEMCAT_CONVERT,
            label=label,
            short_desc=desc,
            target="convertcurrency",
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.NOARGS)

    def _create_result_item(self, label, short_desc, target):
        return self.create_item(
            category=self.ITEMCAT_RESULT,
            label=label,
            short_desc=short_desc,
            target=target,
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.NOARGS,
            data_bag=label)

    def _read_config(self):
        def _warn_cur_code(name, fallback):
            fmt = (
                "Invalid {} value in config. " +
                "Falling back to default: {}")
            self.warn(fmt.format(name, fallback))

        settings = self.load_settings()

        self.always_evaluate = settings.get_bool(
            "always_evaluate",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_ALWAYS_EVALUATE)

        # [default_item]
        self.default_item_enabled = settings.get_bool(
            "enable",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_ITEM_ENABLED)
        self.default_item_label = settings.get_stripped(
            "item_label",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_ITEM_LABEL)

        update_freq_string = settings.get_enum(
            'update_freq',
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_UPDATE_FREQ,
            enum = [freq.value for freq in UpdateFreq]
        )
        self.update_freq = UpdateFreq(update_freq_string)

        path = self.get_package_cache_path(create=True)
        self.broker = ExchangeRates(path, self.update_freq)

        # default input currency
        input_code = settings.get_stripped(
            "input_cur",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_CUR_IN)
        validated_input_code = self.broker.validate_codes(input_code)

        if not validated_input_code:
            _warn_cur_code("input_cur", self.DEFAULT_CUR_IN)
            self.default_cur_in = self.broker.format_codes(self.DEFAULT_CUR_IN)
        else:
            self.default_cur_in = validated_input_code

        # default output currency
        output_code = settings.get_stripped(
            "output_cur",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_CUR_OUT)
        validated_output_code = self.broker.validate_codes(output_code)

        if not validated_output_code:
            _warn_cur_code("output_cur", self.DEFAULT_CUR_OUT)
            self.default_cur_out = self.broker.format_codes(self.DEFAULT_CUR_OUT)
        else:
            self.default_cur_out = validated_output_code
