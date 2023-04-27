import unittest
from botanix.handling import HandlingContext, MainHandler, BaseHandler, HandlingResult
from tests import DictionaryBasedContextRepo
from telegram import Update, Message
from datetime import datetime


class Command1Handler(BaseHandler):

  def handle(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.terminal_result()

class Command2Handler(BaseHandler):

  def handle(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.terminal_result()



class SimpleWorkflowTests(unittest.TestCase):

  def test_simple_workflow(self):
    h = MainHandler(DictionaryBasedContextRepo(), Command1Handler(), Command2Handler())
    r1 = h.handle(123, '/Command1', None)
    self.assertEqual(True, r1.handled)
    self.assertEqual(True, r1.is_terminal)
    r2 = h.handle(123, '/Command2', None)
    self.assertEqual(True, r2.handled)
    self.assertEqual(True, r2.is_terminal)
