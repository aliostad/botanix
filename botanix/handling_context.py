from decimal import Decimal
import json
from botanix.conversion_helper import *

class HandlingContext:
  def __init__(self, uid:int, track_name:str):
    self.uid = uid
    self.track_name = track_name
    self.custom = {}
    self.timestamp = get_time_as_decimal()

  def add_custom(self, key:str, val):
    self.custom[key] = val

  def get_custom(self, key:str):
    return self.custom[key]

  def to_string(self) -> str:
    cop = self.__dict__.copy()
    decimal_to_int_for_shallow_graph(cop)
    return json.dumps(cop)

  @staticmethod
  def from_string(json_s:str):
    dic = json.loads(json_s)
    ctx = HandlingContext(123, 'dummy')
    ctx.__dict__ = dic
    ctx.timestamp = Decimal(ctx.timestamp)
    return ctx