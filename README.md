# jasper-stocks
A module for [jasper-clent](https://github.com/jasperproject/jasper-client) used to retrieve information on stocks.

## Dependencies:
- [jasper-utils](https://github.com/dmbuchta/jasper-utils.git)
- pip install googlefinance

## Installation
``` 
git clone https://github.com/dmbuchta/jasper-stocks.git
ln -s  <absolute path>/jasper-stocks/Stocks.py ~/jasper/client/modules/Stocks.py
```

## Using watchlist.csv
Since STT engines will have trouble transcribing stock symbols and to avoid having to spell out a 
symbol to jasper in order to get a stock quote, a csv file is used to map stock symbols to keywords. 
Please take a look at the file before usage to understand how jasper will look up quotes.
```
cp <absolute path>/jasper-stocks/watchlist.csv ~/.jasper/symbols/watchlist.csv
```
**NOTE:** Copying this file is not necessary, 
but Jasper will not look up any stock symbols that has not been added to the watchlist.csv

## Usage
```
YOU: How is apple doing today?
JASPER: Apple is at XXX.XX
```
```
YOU: Add symbol to my portfolio
JASPER: What symbol would you like to add?
YOU: G-O-O-G-L
JASPER: What keyword would you like to associate this with?
YOU: google
```
```
YOU: How is my portfolio doing?
JASPER: Apple is at XXX.XX
JASPER: Google is at XXX.XX
```
