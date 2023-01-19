import unittest
from botanix.handling_context import HandlingContext

class SerialisationTestCase(unittest.TestCase):

  def test_serial(self):
    ctx = HandlingContext(123, 'can')
    ctx.add_custom('one', 2)
    s = ctx.to_string()
    print(s)
    ctx2 = HandlingContext.from_string(s)
    self.assertEqual(ctx.timestamp, ctx2.timestamp)
    self.assertEqual(ctx.uid, ctx2.uid)
    self.assertEqual(ctx.track_name, ctx2.track_name)
    self.assertEqual(ctx.get_custom('one'), ctx2.get_custom('one'))
