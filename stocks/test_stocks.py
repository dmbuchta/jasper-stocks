# -*- coding: utf-8 -*-
import unittest
from jasper import testutils, diagnose
from . import stocks


class TestStocksPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = testutils.get_plugin_instance(
            stocks.StocksPlugin)

    def test_is_valid_method(self):
        self.assertTrue(self.plugin.is_valid(
            "What is on Portfolio?"))
        self.assertTrue(self.plugin.is_valid(
            "What's on my Portfolio?"))
        self.assertTrue(self.plugin.is_valid(
            "How is my Portfolio doing?"))
        self.assertTrue(self.plugin.is_valid(
            "How is Apple doing?"))
        self.assertTrue(self.plugin.is_valid(
            "How is Apple and Fedex doing?"))
        self.assertTrue(self.plugin.is_valid(
            "Add Symbol"))
        self.assertTrue(self.plugin.is_valid(
            "Remove Symbol"))
        self.assertFalse(self.plugin.is_valid("What time is it?"))

    def test_no_response_handle_method(self):
        mic = testutils.TestMic()
        self.plugin.handle("Something about my portfolio", mic)
        self.assertTrue(len(mic.outputs) == 2)
        self.assertTrue(
            "Would you like to do something with your portfolio?" in mic.outputs)
        self.assertFalse(
            "Is there anything else you would like to do?" in mic.outputs)

    def test_adding_duplicate_symbol(self):
        inputs = ["AAPL", "YES"]
        mic = testutils.TestMic(inputs)
        self.plugin.handle("Add Symbol", mic)
        self.assertTrue(len(mic.outputs) == 5)
        self.assertTrue(
            "What symbol would you like to add?" in mic.outputs)
        self.assertTrue(
            type(mic.outputs[1]) == list)
        self.assertTrue(
            "AAPL is already in your portfolio" in mic.outputs)
        self.assertTrue(
            "Is there anything else you would like to do?" in mic.outputs)

    def test_adding_duplicate_keyword(self):
        inputs = ["TESTDUPLICATEKEYWORD", "YES", "APPLE", "YES"]
        mic = testutils.TestMic(inputs)
        self.plugin.handle("Add Symbol", mic)

        self.assertTrue(len(mic.outputs) == 7)
        self.assertTrue(
            "What keyword would you like to associate this with?" in mic.outputs)
        self.assertTrue(
            "Did you say APPLE" in mic.outputs)
        self.assertTrue(
            "APPLE is already in your portfolio" in mic.outputs)
        self.assertTrue(
            "Is there anything else you would like to do?" in mic.outputs)

    def test_list_portfolio_handle_method(self):
        inputs = ["List Portfolio"]
        mic = testutils.TestMic(inputs)
        self.plugin.handle("Something about my portfolio", mic)
        self.assertTrue(
            type(mic.outputs[1]) == list)
        self.assertTrue(
            type(len(mic.outputs[1])) > 1)
        self.assertTrue("APPLE" in mic.outputs[1])
        self.assertTrue(
            "Is there anything else you would like to do?" in mic.outputs)

    @unittest.skipIf(not diagnose.check_network_connection(),
                     "No internet connection")
    def test_check_portfolio_handle_method(self):
        inputs = ["How is my Portfolio doing?"]
        mic = testutils.TestMic(inputs)
        self.plugin.handle("Something about my portfolio", mic)
        self.assertTrue(
            type(mic.outputs[1]) == list)
        self.assertTrue("APPLE is at" in " ".join(mic.outputs[1]))
        self.assertTrue(
            "Is there anything else you would like to do?" in mic.outputs)

    @unittest.skipIf(not diagnose.check_network_connection(),
                     "No internet connection")
    def test_check_symbol_handle_method(self):
        inputs = []
        mic = testutils.TestMic(inputs)
        self.plugin.handle("How is Apple doing?", mic)
        self.assertTrue(
            type(mic.outputs[0]) == list)
        self.assertTrue(
            len(mic.outputs[0]) == 1)
        self.assertTrue("APPLE is at" in " ".join(mic.outputs[0]))

    def test_canceling_ask_for_symbol_method(self):
        inputs = ["AAPL", "", "NO", "AAPL", "cancel"]
        mic = testutils.TestMic(inputs)
        self.assertFalse(self.plugin.ask_for_symbol(mic))
        self.assertTrue(
            type(mic.outputs[1]) == list)
        self.assertTrue(
            type(mic.outputs[4]) == list)
        self.assertTrue(
            "Could you say that again?" in mic.outputs)

    def test_no_response_ask_for_symbol_method(self):
        inputs = []
        mic = testutils.TestMic(inputs)
        self.assertFalse(self.plugin.ask_for_symbol(mic))
        self.assertTrue(len(mic.outputs) == 3)

    def test_adding_and_removing_symbol(self):
        inputs = ["Add Symbol", "TESTSYMBOL", "yes", "TESTKEYWORD", "yes",
                  "List Portfolio", "Remove Symbol", "TESTKEYWORD", "yes",
                  "List Portfolio"]
        mic = testutils.TestMic(inputs)
        self.plugin.handle("Something about my portfolio", mic)
        self.assertTrue(len(mic.outputs) == 14)
        self.assertTrue(
            type(mic.outputs[2]) == list)
        self.assertTrue(
            type(mic.outputs[6]) == list)
        self.assertTrue(
            type(mic.outputs[11]) == list)
        self.assertTrue(" TESTKEYWORD" in " ".join(mic.outputs[6]))
        self.assertFalse(" TESTKEYWORD" in " ".join(mic.outputs[11]))
