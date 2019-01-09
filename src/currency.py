# Keypirinha launcher (keypirinha.com)

import keypirinha as kp
import keypirinha_util as kpu

from .parser import make_parser, ParserProperties
from .parsy import ParseError
from .exchange import ExchangeRates, UpdateFreq, CurrencyError


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
    ALIAS_SECTION = 'aliases'

    DEFAULT_ITEM_ENABLED = True
    DEFAULT_UPDATE_FREQ = 'daily'
    DEFAULT_ALWAYS_EVALUATE = True
    DEFAULT_ITEM_LABEL = 'Convert Currency'
    DEFAULT_SEPARATORS = 'to, in, :'
    DEFAULT_DESTINATION_SEPARATORS = 'and; &, ,'

    default_item_enabled = DEFAULT_ITEM_ENABLED
    update_freq = UpdateFreq(DEFAULT_UPDATE_FREQ)
    always_evaluate = DEFAULT_ALWAYS_EVALUATE
    default_item_label = DEFAULT_ITEM_LABEL

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
        # This is at top level
        if not items_chain or items_chain[-1].category() != self.ITEMCAT_CONVERT:
            if not self.always_evaluate:
                return
            try:
                query = self._parse_and_merge_input(user_input, True)
                # This tests whether the user entered enough information to
                # indicate a currency conversion request.
                if not self._is_direct_request(query):
                    return
                # if the conversion would have failed, return now
                self.broker.convert(self._parse_and_merge_input(user_input))
            except Exception as e:
                return

        if self.should_terminate(0.25):
            return
        try:
            query = self._parse_and_merge_input(user_input)
            if query['destinations'] is None or query['sources'] is None:
                return

            if self.broker.tryUpdate():
                self._update_update_item()

            if self.broker.error:
                suggestions.append(self.create_error_item(
                    label=user_input,
                    short_desc="Webservice failed ({})".format(self.broker.error)))
            else:
                results = self.broker.convert(query)

                for result in results:
                    suggestions.append(self._create_result_item(
                        label=result['title'],
                        short_desc=result['description'],
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

    def _is_direct_request(self, query):
        entered_dest = ('destinations' in query and
                        query['destinations'] is not None)
        entered_source = (query['sources'] is not None and
                          len(query['sources']) > 0 and
                          query['sources'][0]['currency'] is not None)

        return entered_dest or entered_source

    def _parse_and_merge_input(self, user_input=None, empty=False):
        if empty:
            query = {}
        else:
            query = {
                'sources': [{'currency': self.broker.default_cur_in, 'amount': 1.0}],
                'destinations': [{'currency': cur} for cur in self.broker.default_curs_out],
                'extra': None
            }

        if not user_input:
            return query

        user_input = user_input.lstrip()

        try:
            parsed = self.parser.parse(user_input)
            if not parsed['destinations'] and 'destinations' in query:
                parsed['destinations'] = query['destinations']
            return parsed
        except ParseError as e:
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

        desc = 'Convert from {} to {}'.format(self.broker.default_cur_in, joinCur(self.broker.default_curs_out))

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
            enum=[freq.value for freq in UpdateFreq]
        )
        self.update_freq = UpdateFreq(update_freq_string)

        path = self.get_package_cache_path(create=True)
        self.broker = ExchangeRates(path, self.update_freq, self)

        # default input currency
        input_code = settings.get_stripped(
            "input_cur",
            section=self.DEFAULT_SECTION,
            fallback=self.broker.in_cur_fallback)
        validated_input_code = self.broker.set_default_cur_in(input_code)

        if not validated_input_code:
            _warn_cur_code("input_cur", self.broker.default_cur_in)

        # default output currency
        output_code = settings.get_stripped(
            "output_cur",
            section=self.DEFAULT_SECTION,
            fallback=self.broker.out_cur_fallback)
        validated_output_code = self.broker.set_default_curs_out(output_code)

        if not validated_output_code:
            _warn_cur_code("output_cur", self.broker.default_curs_out)

        # separators
        separators_string = settings.get_stripped(
            "separators",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_SEPARATORS)
        separators = separators_string.split()

        # destination_separators
        dest_seps_string = settings.get_stripped(
            "destination_separators",
            section=self.DEFAULT_SECTION,
            fallback=self.DEFAULT_DESTINATION_SEPARATORS)
        dest_separators = dest_seps_string.split()

        # aliases
        keys = settings.keys(self.ALIAS_SECTION)
        for key in keys:
            try:
                validatedKey = self.broker.validate_code(key)
                aliases = settings.get_stripped(
                    key,
                    section=self.ALIAS_SECTION,
                    fallback=''
                ).split()
                for alias in aliases:
                    validated = self.broker.validate_alias(alias)
                    if validated:
                        self.broker.add_alias(validated, validatedKey)
                    else:
                        fmt = 'Alias {} is invalid. It will be ignored'
                        self.warn(fmt.format(alias))
            except Exception:
                fmt = 'Key {} is not a valid currency. It will be ignored'
                self.warn(fmt.format(key))

        properties = ParserProperties()
        properties.to_keywords = separators
        properties.sep_keywords = dest_separators
        self.parser = make_parser(properties)
