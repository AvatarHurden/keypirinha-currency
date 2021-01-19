# Keypirinha Plugin: Currency

This is Currency, a currency converter plugin for the
[Keypirinha](http://keypirinha.com) launcher.

## Download

https://github.com/AvatarHurden/keypirinha-currency/releases


## Install

Once the `Currency.keypirinha-package` file is installed,
move it to the `InstalledPackage` folder located at:

* `Keypirinha\portable\Profile\InstalledPackages` in **Portable mode**
* **Or** `%APPDATA%\Keypirinha\InstalledPackages` in **Installed mode** (the
  final path would look like
  `C:\Users\%USERNAME%\AppData\Roaming\Keypirinha\InstalledPackages`)

## Usage

A `Convert Currency` item is inserted into the catalog.
Select this item to enter conversion mode.

For the most basic usage, simply enter the amount to convert, the source currency and the destination currency, such as `5 USD in EUR`.
You can perform mathematical operations for the source amount, such as `10*(2+1) usd in EUR`, and you can even perform some math on the resulting amount `5 usd in EUR / 2`.

Furthermore, you can add (or subtract) multiple currencies together, such as `5 USD + 2 GBP in EUR`.
You can also convert into multiple destination currencies, such as `5 USD in EUR, GBP`, and each conversion will be displayed as a separate result.

If you omit the name of a currency, such as in `5 USD` or `5 in USD`, the plugin will use the default currencies specified in the configuration file.
You can also change what words and symbols are used between multiple destination currencies and between the source and destination.

### Aliases

By default, the plugin operates only on [ISO currency codes](https://pt.wikipedia.org/wiki/ISO_4217) (and a few others).
However, there is support for *aliases*, which are alternative names for currencies.
In the configuration file, the user can specify as many aliases as they desire for any currency (for instance, `dollar` and `dollars` for USD).
Aliases, just like regular currency codes, are case-insensitive (i.e. `EuR`, `EUR` and `eur` are all treated the same).


### Math

The available mathematical operations are addition (`+`), subtraction (`-`), multiplication (`*`), division (`/`) and exponentiation (`**` or `^`).
You can also use parentheses and the negative operator (`-(3 + 4) * 4`, for example).

### Grammar

For those familiar with BNF grammars and regex, below is grammar accepted by the parser (`prog` is the top-level expression):

```
prog := sources (to_key? destinations)? extra?

to_key := 'to' | 'in' | ':'

destinations := cur_code sep destinations | cur_code

sep := ',' | '&' | 'and'
cur_code := ([^0-9\s+-/*^()]+)
  # excluding any words that are used as 'sep' or 'to_key'

extra := ('+' | '-' | '*' | '/' | '**' | '^' ) expr

sources := source ('+' | '-') sources | source
source := '(' source ')'
      | cur_code expr
      | expr (cur_code?)

expr := add_expr
add_expr := mult_expr | add_expr ('+' | '-') mult_expr
mult_expr := exp_expr | mult_expr ('*' | '/') exp_expr
exp_expr := unary_expr | exp_expr ('^' | '**') unary_expr
unary_expr := operand | ('-' | '+') unary_expr
operand := number | '(' expr ')'

number := (0|[1-9][0-9]*)([.,][0-9]+)?([eE][+-]?[0-9]+)?
```

## Backend

The Currency plugin uses [OpenExchangeRates](https://openexchangerates.org/) to obtain hourly exchange rates for all currencies. Since this project does not make any money, it is using the free tier, which only allows 1000 requests per month. In order to allow the most number of people to use the plugin without any work, there is a cache layer that reduces the number of requests to the backend. 

If this cache layer fails, however, the plugin quickly runs into this request limit. In order to work around this issue, the plugin allows users to specify their own App ID to use whenever the cache is older than 2 hours. This shouldn't happen often, but is a safeguard in case things go wrong. Users can get a free App ID by creating an account [here](https://openexchangerates.org/signup/free).

## Change Log

### v2.2
* Added workaround for situations in which the cache fails.

### v2.1

* Improved grammar for more intuitive use
* Bug fixes
* Improved options to copy results to clipboard

### v2.0

* Improved parser. More flexible, and now you can specify your own separators in the config file
* Math! Add, subtract, multiply, or divide numbers to obtain the source amount for a currency (also supports parentheses and exponents)
* Multiple source currencies. Add or subtract amounts in different currencies to obtain a final result
* An icon
* Support for aliases. The user can create aliases ('nicknames') for any valid currency in the config file


### v1.4

* Added a layer between clients and OpenExchangeRates to mitigate API usage

### v1.3

* Changed API from Yahoo Finance to OpenExchangeRates

### v1.2

* Saves exchange information locally, updating automatically or manually
* Allow converting currencies directly in the search

### v1.1

* Allow decimal amounts to be inserted (using either a comma or a period)
* Added copy actions
* Added configuration for default currencies
* Multiple source and destination currencies can be specified

### v1.0

* Initial Release


## License

This package is distributed under the terms of the MIT license.

## Contribute

1. Check for open issues or open a fresh issue to start a discussion around a
   feature idea or a bug.
2. Fork this repository on GitHub to start making your changes to the **dev**
   branch.
3. Send a pull request.
4. Add yourself to the *Contributors* section below (or create it if needed)!
