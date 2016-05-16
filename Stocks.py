from googlefinance import getQuotes
import json
from utils.mic_utils import MicUtils
import re
import jasperpath
import csv

PRIORITY = 2
# ARSENAL and ASSEMBLE have been added because they sound like "Add Symbol"
WORDS = ["PRICE", "(add\s)?STOCK", "(add\s)?SYMBOL", "PORTFOLIO", "WATCH(\s)?LIST", "ARSENAL", "ASSEMBLE"]
# compiled is_valid regex
IS_VALID = re.compile(r"\b(%s)\b" % "|".join(WORDS), re.IGNORECASE)

# Used to check how the entire watchlist is doing (e.g. How is my portfolio doing?)
CHECK_PORTFOLIO = re.compile(r"\bhow\b", re.IGNORECASE)
# Used to list the entire watchlist keywords(e.g. What is on my portfolio?)
LIST_PORTFOLIO = re.compile(r"\bwhat|list\b", re.IGNORECASE)
# Used to add a symbol to the portfolio (e.g. Add symbol)
ADD_TO_PORTFOLIO = re.compile(r"\b(ad(d)?|and|head|ab(s)?|heart|at)\b", re.IGNORECASE)
# Used to remove a symbol to the portfolio (e.g. Remove symbol)
REMOVE_FROM_PORTFOLIO = re.compile(r"\b(remove|forget|delete)\b", re.IGNORECASE)
# Index used in retrieving keyword from csv file
PORTFOLIO_KEYWORD_INDEX = 1
# Index used in retrieving symbol from csv file
PORTFOLIO_SYMBOL_INDEX = 0
# This will be the compiled regex pattern for all the keywords in the watchlist
PORTFOLIO_KEYWORDS = None

# Read the csv file and load the watchlist into memory
try:
    csvFile = open(jasperpath.config('symbols/watchlist.csv'), 'rb')
    reader = csv.reader(csvFile)
    WATCH_LIST = {item[PORTFOLIO_SYMBOL_INDEX]: item[PORTFOLIO_KEYWORD_INDEX] for item in list(reader)}
except:
    WATCH_LIST = {}


def compilePortfolioPattern():
    """
        Compiles the keywords in the WATCH_LIST dictionary
    """
    global PORTFOLIO_KEYWORDS
    if len(WATCH_LIST):
        PORTFOLIO_KEYWORDS = re.compile(r"\b(%s)\b" % "|".join(WATCH_LIST.values()), re.IGNORECASE)
    else:
        # Impossible to match regex
        PORTFOLIO_KEYWORDS = re.compile('a^')


compilePortfolioPattern()


def getKeyWord(mic, question, confirmation):
    """
        Asks user the supplied question, and then states the confimation question
        Will run until the user confirms or cancels the keyword
    """
    while True:
        word = mic.ask(question)
        if mic.checkForCancel():
            return
        mic.sayLesser(confirmation + word)
        while True:
            mic.activeListen()
            if mic.checkForDeny():
                break;
            elif mic.checkForConfirm():
                return word.upper()
            elif mic.checkForCancel():
                return
            mic.sayLesser("Could you say that again?")


def addToPortfolio(mic):
    """
        Used to add a key:symbol to the watchlist
        upon success, writes the new pair to the watchlist.csv file
    """
    def getSymbol():
        while True:
            symbol = mic.ask("What symbol would you like to add?")
            if mic.checkForCancel():
                return
            mic.sayLesser("Did you say")
            mic.say(list(symbol))
            while True:
                mic.activeListen()
                if mic.checkForDeny():
                    break;
                elif mic.checkForConfirm():
                    return symbol.upper()
                elif mic.checkForCancel():
                    return
                mic.sayLesser("Could you say that again?")

    def add(newSymbol, keyword):
        try:
            csvFile = open(jasperpath.config('symbols/watchlist.csv'), 'a+b')
        except IOError:
            mic.say("I could not open your watch list for some reason")
            return False
        else:
            spamwriter = csv.writer(csvFile, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            spamwriter.writerow([newSymbol, keyword])
            WATCH_LIST[newSymbol] = keyword
            compilePortfolioPattern()
            return True

    newSymbol = getSymbol()
    if newSymbol in WATCH_LIST.keys():
        mic.sayLesser(newSymbol + " is already in your watch list")
        return True

    if newSymbol:
        keyword = getKeyWord(mic, "What keyword would you like to associate this with?", "Did you say ")
        if keyword in WATCH_LIST.values():
            mic.sayLesser(keyword + " is already in your watch list")
            return True

        if keyword:
            return add(newSymbol, keyword)


def removeFromPortfolio(mic):
    """
        Removes a symbol from the watchlist
         upon success, rewrites the watchlist.csv file
    """
    def removeFromMemory():
        for (key, value) in WATCH_LIST.iteritems():
            if key == keyword or value == keyword:
                del WATCH_LIST[key]
                return True

    def rewriteFile():
        try:
            csvFile = open(jasperpath.config('symbols/watchlist.csv'), 'w+b')
        except IOError:
            mic.say("I could not open your watch list for some reason")
            return False
        else:
            spamwriter = csv.writer(csvFile, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for (key, value) in WATCH_LIST.iteritems():
                spamwriter.writerow([key, value])
            return True

    keyword = getKeyWord(mic, "What symbol would you like to remove?", "Are you sure you would like to remove ")
    if keyword:
        if removeFromMemory():
            if rewriteFile():
                compilePortfolioPattern()
                return True
            return False
        mic.sayLesser(keyword + " is not in your watch list")
        return True


def getQuotesFromAPI(mic, keywords):
    """
        Retrieves quotes from the googlefinance api
        using the mapped symbol from the provided keywords
    """
    symbols = [key for (key, value) in WATCH_LIST.iteritems() if value in keywords]
    quotes = getQuotes(symbols)
    if len(quotes):
        spokenQuotes = []
        for quote in quotes:
            spokenQuotes.append(WATCH_LIST[str(quote["StockSymbol"]).upper()] + " is at " + quote["LastTradePrice"])
        mic.say(spokenQuotes)
    else:
        mic.sayLesser("It appears I am having trouble looking up your quote")
    return True


def listPortfolio(mic):
    """
        Lists all the keywords that are stored in the watchlist
    """
    mic.sayLesser("Your porfolio is comprised of ")
    mic.say(WATCH_LIST.values())
    return True


def handle(text, mic, profile=None):
    mic = MicUtils(mic)
    doContinue = True
    firstTimeHandling = True
    while True:
        if not text:
            text = ""
        saidKeywords = PORTFOLIO_KEYWORDS.findall(text)
        if len(saidKeywords) > 0:
            # must convert unicode to string
            doContinue = getQuotesFromAPI(mic, [str(x).upper() for x in saidKeywords])
        elif bool(ADD_TO_PORTFOLIO.search(text)):
            doContinue = addToPortfolio(mic)
        elif bool(REMOVE_FROM_PORTFOLIO.search(text)):
            doContinue = removeFromPortfolio(mic)
        elif bool(CHECK_PORTFOLIO.search(text)):
            doContinue = getQuotesFromAPI(mic, WATCH_LIST.values())
        elif bool(LIST_PORTFOLIO.search(text)):
            doContinue = listPortfolio(mic)
        elif firstTimeHandling:
            text = mic.ask("Would you like to do something with your portfolio?", False)
            doContinue = False
            firstTimeHandling = False
            continue

        if doContinue:
            text = mic.ask("Is there anything else you would like to do?", False)
            doContinue = False
        else:
            mic.sayLesser("Alright then.")
            break

        firstTimeHandling = False


def isValid(text):
    return bool(IS_VALID.search(text)) or bool(PORTFOLIO_KEYWORDS.search(text))
