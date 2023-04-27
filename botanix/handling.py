import json
from botanix.conversion_helper import *
from telegram import Update
import inspect
import re


class UnhandledMessage(Exception):
  def __init__(self, *args):
    super().__init__(args)


class HandlingContext:
  def __init__(self, uid:int, track_name:str, step:int=0):
    self.uid = uid
    self.track_name = track_name
    self.custom = {}
    self.timestamp = get_time_as_decimal()
    self.step = step

  def put_custom(self, key:str, val):
    """
    Puts a custom value in the context
    :param key:
    :param val: must be serialisable
    :return:
    """
    self.custom[key] = val

  def move_to_next(self):
    self.step += 1

  def override_step(self, step:int):
    self.step = step

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


# Handlers return HandlingResult at the end of handling
# They can define one of the statuses below:
#   1) Not handling the message/update which means the message will be passed to the next handler if one exists
#   2) Handling the message/update and letting it run one step higher (step + 1)
#   3) Handling but overriding the next step, jumping to a much higher step or lower
#   4) Handling it and saying that it is terminal and no more interaction are required
#   5) Handling it and changing the track while changing the step as well
class HandlingResult:
  def __init__(self, handled:bool=False, unhandled_message:str=None,
               is_terminal:bool=False, step_override:int=None,
               new_track_name:str=None):
    self.handled = handled
    self.unhandled_message = unhandled_message
    self.is_terminal = is_terminal
    self.step_override = step_override
    self.new_track_name = new_track_name

  @staticmethod
  def success_result():
    return HandlingResult(handled=True)

  @staticmethod
  def unhandled_result(message:str):
    return HandlingResult(unhandled_message=message)

  @staticmethod
  def terminal_result():
    return HandlingResult(handled=True, is_terminal=True)

  @staticmethod
  def override_step_result(new_step:int):
    return HandlingResult(handled=True, step_override=new_step)


  @staticmethod
  def new_track_result(new_track_name:str, new_step:int):
    return HandlingResult(handled=True, step_override=new_step, new_track_name=new_track_name)

# This is the base class for handlers. A handler class will inherit BaseHandler
# will implement all functionality of a track.
# The name of the class must be `<track name>Handler` e.g. command
# /register will load RegisterHandler
# This class will handle ALL its steps by creating one or more methods for each step, with a
# signature similar to `handle` method here:
#     (self, command: str, update: Update, context: dict) -> HandlingResult
# The method can have any name but needs to end with _<step number>.
# The level the user is at would then matched to the step of the track.
# At runtime, all these methods will be discovered (when main handler calls `ensure_tracks_built`)
# Steps within the track will be routed via the _<n> (where <n> is step) in the name
#
#
class BaseHandler:
  handler_method_pattern = '[_A-Za-z0-9]+_(\d+)'

  def __init__(self):
    self.step_handlers = None

  def handle(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
    self.ensure_tracks_built()
    uid = context.uid
    step = context.step
    if step not in self.step_handlers:
      raise UnhandledMessage(
        f'Step {step} does not exist in class {self.__class__.__name__}. Command was {command} and user id {uid}')
    last_result = HandlingResult.success_result()
    for h in self.step_handlers[step]:
      last_result = h(command, update, context)
      if last_result.handled:
        return last_result # break out
    return last_result

  def get_class_name(self):
    return self.__class__.__name__.lower().replace('handler', '')

  def ensure_tracks_built(self):
    if self.step_handlers is not None:
      return
    self.step_handlers = {}
    for name, func in inspect.getmembers(self, inspect.ismethod):
      m = re.match(BaseHandler.handler_method_pattern, name)
      if m is not None:
        step = int(m.groups()[0])
        if step not in self.step_handlers:
          self.step_handlers[step] = []
        self.step_handlers[step].append(func)


class BaseContextRepo:
  """
  Main interface for context repository
  """
  def get_active_context(self, uid: int) -> HandlingContext:
    """
    Returns active contex
    :param uid:
    :return:
    """
    pass

  def new_context(self, uid: int, track_name: str) -> HandlingContext:
    """
    Creates, stores and returns a new context
    :param uid:
    :param track_name:
    :return:
    """
    pass

  def put_context(self, uid: int, context: HandlingContext) -> None:
    """
    Updates the stored context
    :param uid:
    :param context:
    :return:
    """
    pass

  def clear_context(self, uid: int):
    """
    Deletes stored context
    :param uid:
    :return:
    """
    pass



class MainHandler:
  command_pattern = '^/([A-Za-z0-9]+)$'  # like /start or /Register
  generic_handler_names = ['help', 'start']

  def __init__(self, repo: BaseContextRepo, *list_of_handlers: BaseHandler):
    self.handlers = {}
    self.repo = repo
    for h in list_of_handlers:
      self.handlers[h.get_class_name()] = h

  def handle(self, uid: int, message_text: str, update: Update) -> HandlingResult:
    message_text = message_text.lower()
    ctx = self.repo.get_active_context(uid)
    m = re.match(MainHandler.command_pattern, message_text)
    if m is None:
      if ctx is None:
        return HandlingResult.unhandled_result('Your choice does not exist.')
      else:
        track_name = ctx.track_name
        if track_name not in self.handlers:
          raise UnhandledMessage(f'Could not find a handler for command {message_text}')
        return self._do_handle(uid, message_text, update, ctx, track_name)
    else:  # this is a top level command (start of a track)
      class_command = m.groups()[0]  # is the same as track_name
      if class_command not in self.handlers:
        raise UnhandledMessage(f'Could not find a handler for command {message_text}')
      if class_command in MainHandler.generic_handler_names:
        ctx = HandlingContext(uid, track_name=class_command) # create a dummy context and not store since they do not have follow up
      else:
        ctx = self.repo.new_context(uid, class_command)  # renew context
      return self._do_handle(uid, message_text, update, ctx, class_command)

  def _do_handle(self, uid: int, command: str, update: Update, context: HandlingContext, class_command: str) -> HandlingResult:
    result = self.handlers[class_command].handle(command, update, context)
    if result.handled and not result.is_terminal:
      if result.step_override is None:
        context.move_to_next()  # increase the step
      else:
        context.override_step(result.step_override)  # change the step
      self.repo.put_context(uid, context)
    if result.is_terminal:
      self.repo.clear_context(uid)
    return result

