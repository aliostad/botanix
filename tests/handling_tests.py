import unittest
from botanix.handling import HandlingContext, MainHandler, BaseHandler, HandlingResult, track_name, step_number
from tests import DictionaryBasedContextStore
from telegram import Update


class Command1Handler(BaseHandler):
  def handle(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.terminal_result()

class Command2Handler(BaseHandler):
  def handle(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.terminal_result()

@track_name('Command3')
class CommandThreeHandler(BaseHandler):
  def handle_0(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.success_result()

  @step_number(1)
  def handle_or_waht(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.success_result()

  def does_not_matter_2(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.terminal_result()


class SimpleWorkflowTests(unittest.TestCase):

  def test_simple_workflow(self):
    h = MainHandler(DictionaryBasedContextStore(), Command1Handler(), Command2Handler())
    r1 = h.handle(123, '/Command1', None)
    self.assertEqual(True, r1.handled)
    self.assertEqual(True, r1.is_terminal)
    r2 = h.handle(123, '/Command2', None)
    self.assertEqual(True, r2.handled)
    self.assertEqual(True, r2.is_terminal)

  def test_3_steps(self):
    h = MainHandler(DictionaryBasedContextStore(),
                    Command1Handler(), Command2Handler(),
                    CommandThreeHandler())
    r1 = h.handle(123, '/Command3', None)
    self.assertEqual(True, r1.handled)
    self.assertEqual(False, r1.is_terminal)
    r2 = h.handle(123, 'doesnt matter!', None)
    self.assertEqual(True, r2.handled)
    self.assertEqual(False, r2.is_terminal)
    r3 = h.handle(123, 'doesnt matter!', None)
    self.assertEqual(True, r3.handled)
    self.assertEqual(True, r3.is_terminal)
