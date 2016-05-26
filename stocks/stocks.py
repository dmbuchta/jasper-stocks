from jasper import plugin
from jasper import paths
from jasper.app_utils import is_cancel, is_negative, is_positive, is_repeat
import csv
import re

from googlefinance import getQuotes

# Sounds like "Add Symbol"
LIKE_VALID_WORDS = ["ARSENAL", "ASSEMBLE", "ENSEMBLE", "ALL SYMBOL",
                    "'A SYMBOL"]
LIKE_ADD_WORDS = ["AD", "AND", "HEAD", "AB", "ABS", "HEART", "AT", "ARSENAL",
                  "ASSEMBLE", "ENSEMBLE", "ALL SYMBOL",
                  "'A SYMBOL"]

# Index used in retrieving keyword from csv file
PORTFOLIO_KEYWORD_INDEX = 1
# Index used in retrieving symbol from csv file
PORTFOLIO_SYMBOL_INDEX = 0
last_thing_said = None


def check_if_valid(phrases, text):
    phrases = re.compile(r"\b(%s)\b" % "|".join(phrases), re.IGNORECASE)
    if type(text) is list or type(text) is tuple:
        text = ", ".join(text)
    return bool(phrases.search(text))


def ask(mic, question, tries_until_break=3):
    while True:
        response = mic.ask(question)
        tries_until_break -= 1
        if tries_until_break <= 0 or (len(response) >= 1 and len(response[0])):
            break
        question = "I couldn't get that"
    if not len(response) or not len(response[0]):
        return False
    if is_repeat(response) and last_thing_said:
        mic.say(last_thing_said)
        return ask(mic, question, tries_until_break)
    return response


def say(mic, statement):
    global last_thing_said
    last_thing_said = statement
    mic.say(last_thing_said)


class StocksPlugin(plugin.SpeechHandlerPlugin):
    def __init__(self, *args, **kwargs):
        super(StocksPlugin, self).__init__(*args, **kwargs)
        try:
            csvFile = open(paths.config('symbols/portfolio.csv'), 'rb')
            reader = csv.reader(csvFile)
            self.portfolio = {
                item[PORTFOLIO_SYMBOL_INDEX]: item[PORTFOLIO_KEYWORD_INDEX] for
                item
                in list(reader)}
        except:
            self.portfolio = {}
        self.compile_portfolio_pattern()

    def compile_portfolio_pattern(self):
        if len(self.portfolio):
            self.portfolio_regex = re.compile(
                r"\b(%s)\b" % "|".join(self.portfolio.values()), re.IGNORECASE)
        else:
            # Impossible to match regex
            self.portfolio_regex = re.compile('a^')

    def ask_for_symbol(self, mic):
        while True:
            symbol = ask(mic, self.gettext(
                "What symbol would you like to add?"))
            if not symbol or is_cancel(symbol):
                return False
            symbol = symbol[0]
            mic.say([self.gettext("Did you say")] + list(symbol))
            while True:
                confirm = mic.active_listen()
                if is_negative(confirm):
                    break;
                elif is_positive(confirm):
                    return symbol.upper()
                elif is_cancel(confirm):
                    return
                elif is_repeat(confirm):
                    mic.say([self.gettext("Did you say")] + list(symbol))
                    continue
                mic.say(self.gettext("Could you say that again?"))

    def ask_for_keyword(self, mic, question, confirmation):
        """
            Asks user the supplied question, and then states the confimation question
            Will run until the user confirms or cancels the keyword
        """
        while True:
            word = ask(mic, self.gettext(question))
            if not word or is_cancel(word):
                return False
            word = word[0]
            mic.say(self.gettext(confirmation) + word)
            while True:
                confirm = mic.active_listen()
                if is_negative(confirm):
                    break;
                elif is_positive(confirm):
                    return word.upper()
                elif is_cancel(confirm):
                    return
                elif is_repeat(confirm):
                    mic.say(self.gettext(confirmation) + word)
                    continue
                mic.say(self.gettext("Could you say that again?"))

    def add_to_csv(self, mic, new_symbol, keyword):
        try:
            csvFile = open(paths.config('symbols/portfolio.csv'),
                           'a+b')
        except IOError:
            mic.say(
                self.gettext("I could not open your portfolio for some reason"))
            return False
        else:
            spam_writer = csv.writer(csvFile, delimiter=',',
                                     quotechar='|',
                                     quoting=csv.QUOTE_MINIMAL)
            spam_writer.writerow([new_symbol, keyword])
            self.portfolio[new_symbol] = keyword
            self.compile_portfolio_pattern()
            return True

    def add_to_portfolio(self, mic):
        """
            Used to add a key:symbol to the portfolio
            upon success, writes the new pair to the portfolio.csv file
        """
        new_symbol = self.ask_for_symbol(mic)
        if new_symbol in self.portfolio.keys():
            mic.say(
                self.gettext("{word} is already in your portfolio").format(
                    word=new_symbol))
            return True

        if new_symbol:
            keyword = self.ask_for_keyword(mic,
                                           "What keyword would you like to associate this with?",
                                           "Did you say ")
            if keyword in self.portfolio.values():
                mic.say(
                    self.gettext("{word} is already in your portfolio").format(
                        word=keyword))
                return True

            if keyword:
                return self.add_to_csv(mic, new_symbol, keyword)

    def get_quotes(self, mic, keywords):
        """
            Retrieves quotes from the googlefinance api
            using the mapped symbol from the provided keywords
        """
        symbols = [key for (key, value) in self.portfolio.iteritems() if
                   value in keywords]
        quotes = getQuotes(symbols)
        if len(quotes):
            formatted_quotes = []
            for quote in quotes:
                formatted_quotes.append(
                    self.gettext("{stock} is at {price}").format(
                        stock=self.portfolio[quote["StockSymbol"].upper()],
                        price=quote[
                            "LastTradePrice"]))
            say(mic, formatted_quotes)
        else:
            mic.say(self.gettext(
                "It appears I am having trouble looking up your quote"))
        return True

    def remove_from_portfolio(self, mic):
        """
            Removes a symbol from the portfolio
             upon success, rewrites the portfolio.csv file
        """
        keyword = self.ask_for_keyword(mic,
                                       "What symbol would you like to remove?",
                                       "Are you sure you would like to remove ")
        if keyword:
            for (key, value) in self.portfolio.iteritems():
                if key == keyword or value == keyword:
                    del self.portfolio[key]
                    keyword = False
                    break
            if not keyword:
                try:
                    csvFile = open(paths.config('symbols/portfolio.csv'),
                                   'w+b')
                except IOError:
                    mic.say(self.gettext(
                        "I could not open your portfolio for some reason"))
                    return False
                else:
                    spam_writer = csv.writer(csvFile, delimiter=',',
                                             quotechar='|',
                                             quoting=csv.QUOTE_MINIMAL)
                    for (key, value) in self.portfolio.iteritems():
                        spam_writer.writerow([key, value])
                    self.compile_portfolio_pattern()
            else:
                mic.say(
                    self.gettext("{word} is not in your portfolio").format(
                        word=keyword))
            return True

    def list_portfolio(self, mic):
        """
            Lists all the keywords that are stored in the portfolio
        """
        say(mic, [self.gettext("Your porfolio is comprised of ")] +
            self.portfolio.values())
        return True

    def get_phrases(self):
        return [self.gettext("STOCK"), self.gettext("SYMBOL"),
                self.gettext("PRICE"), self.gettext("PORTFOLIO"),
                self.gettext("WATCH LIST")] + LIKE_VALID_WORDS

    def get_phrases_for_adding(self):
        return [self.gettext("ADD")] + LIKE_ADD_WORDS

    def get_phrases_for_listing(self):
        return [self.gettext("WHAT"), self.gettext("LIST")]

    def get_phrases_for_removal(self):
        return [self.gettext("REMOVE"), self.gettext("FORGET"),
                self.gettext("DELETE")]

    def get_phrases_for_checking(self):
        return [self.gettext("HOW")]

    def handle(self, text, mic):
        """
        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        """
        global last_thing_said
        last_thing_said = None
        do_continue = True
        first_time = True
        text = [text]
        while True:
            if not text:
                text = ""
                said_keywords = ""
            else:
                said_keywords = self.portfolio_regex.findall(", ".join(text))
            if len(said_keywords):

                do_continue = self.get_quotes(mic, [x.upper() for x in
                                                    said_keywords])
            elif check_if_valid(self.get_phrases_for_removal(), text):
                do_continue = self.remove_from_portfolio(mic)
            elif check_if_valid(self.get_phrases_for_adding(), text):
                do_continue = self.add_to_portfolio(mic)
            elif check_if_valid(self.get_phrases_for_listing(), text):
                do_continue = self.list_portfolio(mic)
            elif check_if_valid(self.get_phrases_for_checking(), text):
                do_continue = self.get_quotes(mic, self.portfolio.values())
            elif first_time:
                text = ask(mic, self.gettext(
                    "Would you like to do something with your portfolio?"),
                           tries_until_break=0)
                do_continue = False
                first_time = False
                continue

            if do_continue:
                text = ask(mic, self.gettext(
                    "Is there anything else you would like to do?"),
                           tries_until_break=0)
                do_continue = False
            else:
                mic.say(self.gettext("Alright then"))
                break
            first_time = False

    def is_valid(self, text):
        """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return check_if_valid(self.get_phrases(), text) or bool(
            self.portfolio_regex.search(text))

    def get_priority(self):
        return 1
