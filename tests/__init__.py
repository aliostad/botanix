from botanix.handling import BaseContextStore, HandlingContext
class DictionaryBasedContextStore(BaseContextStore):

  def __init__(self):
    self.contexts = {}

  def get_active_context(self, uid: int) -> HandlingContext:
    """
    Returns active contex
    :param uid:
    :return:
    """
    if uid in self.contexts:
      return self.contexts[uid]
    else:
      return None

  def new_context(self, uid: int, track_name: str) -> HandlingContext:
    """
    Creates, stores and returns a new context
    :param uid:
    :param track_name:
    :return:
    """
    self.contexts[uid] = HandlingContext(uid, track_name)
    return self.contexts[uid]

  def put_context(self, uid: int, context: HandlingContext) -> None:
    """
    Updates the stored context
    :param uid:
    :param context:
    :return:
    """
    self.contexts[uid] = context

  def clear_context(self, uid: int):
    """
    Deletes stored context
    :param uid:
    :return:
    """
    self.contexts.clear()