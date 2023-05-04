import unittest
from botanix.handling import HandlingContext, MainHandler, BaseHandler, HandlingResult, track_name, step_number
from tests import DictionaryBasedContextStore
from telegram import Update

class Command1Handler(BaseHandler):
  async def handle_0(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.terminal_result()

class Command2Handler(BaseHandler):
  async def handle_0(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.terminal_result()

@track_name('Command3')
class CommandThreeHandler(BaseHandler):
  async def handle_0(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.success_result()

  @step_number(1)
  async def handle_or_waht(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.success_result()

  async def does_not_matter_2(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.terminal_result()

  @step_number(2)
  async def i_said_does_not_matter(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    return HandlingResult.terminal_result()

class SimpleWorkflowTests(unittest.IsolatedAsyncioTestCase):

  async def test_simple_workflow(self):
    h = MainHandler(DictionaryBasedContextStore(), Command1Handler(), Command2Handler())
    r1 = await h.handle(123, '/Command1', None)
    self.assertEqual(True, r1.handled)
    self.assertEqual(True, r1.is_terminal)
    r2 = await h.handle(123, '/Command2', None)
    self.assertEqual(True, r2.handled)
    self.assertEqual(True, r2.is_terminal)

  async def test_3_steps(self):
    h = MainHandler(DictionaryBasedContextStore(),
                    Command1Handler(), Command2Handler(),
                    CommandThreeHandler())
    r1 = await h.handle(123, '/Command3', None)
    self.assertEqual(True, r1.handled)
    self.assertEqual(False, r1.is_terminal)
    r2 = await h.handle(123, 'doesnt matter!', None)
    self.assertEqual(True, r2.handled)
    self.assertEqual(False, r2.is_terminal)
    r3 = await h.handle(123, 'doesnt matter!', None)
    self.assertEqual(True, r3.handled)
    self.assertEqual(True, r3.is_terminal)

  async def test_handler(self):
    h = CommandThreeHandler()
    result = await h.handle('n', None, HandlingContext(123, 'n'))
    self.assertEqual(1, len(h.step_handlers[0]))
    self.assertEqual(1, len(h.step_handlers[1]))
    self.assertEqual(2, len(h.step_handlers[2]))
