import datetime
from decimal import Decimal
import dateutil.parser

def get_time_as_decimal(dt:datetime.datetime=None) -> Decimal:
  if dt is None:
    dt = datetime.datetime.utcnow()
  return Decimal(round(dt.timestamp()))

def get_decimal_as_time(value:Decimal) -> datetime.datetime:
  return datetime.datetime.fromtimestamp(float(value))

def parse_iso(date_str:str) -> datetime.datetime:
  return dateutil.parser.parse(date_str)

def decimal_to_int_for_shallow_graph(obj:dict):
  for k in obj:
    if type(obj[k]) == Decimal:
      obj[k] = int(obj[k])
  return obj