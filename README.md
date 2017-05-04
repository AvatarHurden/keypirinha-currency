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

A ```Convert Currency``` item is inserted into the catalog with conversion from USD to BRL.
Select this item to enter conversion mode.

Enter the amount to convert, the source currency code and the destination currency code.
If either the source and destination currency is omitted, the defaults are used.
If the amount is omitted, the current exchange rate is shown.

*Currency* allows the source and destination currencies to be separated by any of the following:
 - in
 - to
 - :

To convert between multiple currencies at the same time, separate each one by a comma.
This can be done in either the source or destination field, and all combinations will be displayed in the results.

This means that all of the following are allowed:

- 5 usd in inr,JPY
- EUR to JPY
- 10 brl,usd:EUR,gbp

## Change Log

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
