from samples import simple_bot
import unittest

class SimpleWorkflowTests(unittest.IsolatedAsyncioTestCase):

  async def test_handler(self):
    h = simple_bot.RegisterHandler(None)
    h.ensure_steps_built()
    self.assertEqual(1, len(h.step_handlers[0]))
    self.assertEqual(1, len(h.step_handlers[1]))
    self.assertEqual(1, len(h.step_handlers[2]))
    self.assertEqual(1, len(h.step_handlers[3]))

