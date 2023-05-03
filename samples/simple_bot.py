import traceback

from botanix.handling import *
from telegram import Bot
import re
import boto3
from botocore.exceptions import ClientError
import json
import os
import asyncio

class HelpHandler(BaseHandler):

  def __init__(self, bot: Bot):
    super().__init__()
    self.bot = bot

  @step_number(0)
  def send_help(self, uid: int, command: str, update: Update,
                context: HandlingContext, class_command: str) -> HandlingResult:
    await self.bot.send_message(context.uid, """
    You may choose:
    /start to start again
    /help to see this menu
    /register to register with us
    """)
    return HandlingResult.success_result()


class StartHandler(BaseHandler):

  def __init__(self, bot: Bot):
    super().__init__()
    self.bot = bot

  @step_number(0)
  def start(self, uid: int, command: str, update: Update,
                context: HandlingContext, class_command: str) -> HandlingResult:
    await self.bot.send_message(context.uid, """
    Welcome to our bot!
    You may choose:
    /start to start again
    /help to see this menu
    /register to register with us
    """)
    return HandlingResult.terminal_result()

class FieldNames:
  FirstName = 'firstName'
  Surname = 'surname'
  Email = 'email'

class RegisterHandler(BaseHandler):

  def __init__(self, bot: Bot):
    super().__init__()
    self.bot = bot

  @step_number(0)
  def ask_for_name(self, uid: int, command: str, update: Update,
                context: HandlingContext, class_command: str) -> HandlingResult:
    await self.bot.send_message(context.uid, "Please enter your first name:")

    return HandlingResult.success_result()

  @step_number(1)
  def ask_for_surname(self, uid: int, command: str, update: Update,
                context: HandlingContext, class_command: str) -> HandlingResult:
    nam = command.strip()
    if len(nam) < 3:
      await self.bot.send_message(context.uid, "First name must be at least 3 characters. Try again.")
      return HandlingResult.unhandled_result("Invalid input")
    else:
      context.custom[FieldNames.FirstName] = nam
      await self.bot.send_message(context.uid, "Please provide your surname:")
      return HandlingResult.success_result()

  @step_number(2)
  def ask_for_email(self, uid: int, command: str, update: Update,
                context: HandlingContext, class_command: str) -> HandlingResult:
    surnam = command.strip()
    if len(surnam) < 3:
      await self.bot.send_message(context.uid, "Surname must be at least 3 characters. Try again.")
      return HandlingResult.unhandled_result("Invalid input")
    else:
      context.custom[FieldNames.Surname] = surnam
      await self.bot.send_message(context.uid, "Please provide your email:")
      return HandlingResult.success_result()

  @step_number(3)
  def ask_for_email(self, uid: int, command: str, update: Update,
                context: HandlingContext, class_command: str) -> HandlingResult:
    email = command.strip()
    if re.match('.+@.+\..+', email) is None:
      await self.bot.send_message(context.uid, "Not a valid email. Try again.")
      return HandlingResult.unhandled_result("Invalid input")
    else:
      register_user(context.custom[FieldNames.FirstName], context.custom[FieldNames.Surname], email)
      await self.bot.send_message(context.uid, "Your registration was successful!")
      return HandlingResult.terminal_result()


def register_user(first_name:str, surname:str, email:str):
  # do whatever is necessary
  pass


# This is a simple implementation. S3 is not necessarily a good choice for storing context. Although
# it supports expiration, it is costly considering many number of operations required per one interaction.
# But considering its simplicity, it is suitable for a sample
class S3ContextStore(BaseContextStore):

  def __init__(self, bucket_name:str, prefix:str=None):
    self.prefix = prefix
    s3 = boto3.resource('s3')
    self.bucket = s3.Bucket(bucket_name)

  def _get_name(self, name:str):
    if self.prefix is None:
      return name
    else:
      return self.prefix + name

  def new_context(self, uid: int, track_nam: str) -> HandlingContext:
    hc = HandlingContext(uid, track_nam)
    o = self.bucket.Object(self._get_name(str(uid)))
    o.put(json.dumps(hc))

  def clear_context(self, uid: int):
    o = self.bucket.Object(self._get_name(str(uid)))
    o.delete()

  def get_active_context(self, uid: int) -> HandlingContext:
    o = self.bucket.Object(self._get_name(str(uid)))
    try:
      jtext = o.get()['Body'].read().decode('utf-8')
      j = json.loads(jtext)
      hc = HandlingContext(j['uid'], j['track_name'], j['step'])
      hc.custom = j['custom']
      return hc
    except ClientError as e:
      print('Vafa!!')
      print(e)
      if e.response['Error']['Code'] == "404":
        return None
      else:
        raise

  def put_context(self, uid: int, context: HandlingContext):
    o = self.bucket.Object(self._get_name(str(uid)))
    o.put(json.dumps(context))

async def do_handle(event, context):
  try:
    if 'BOT_TOKEN' not in os.environ:
      print('Bot token env var not defined.')
      exit(-1)
    body = event['body']
    bot = Bot(os.environ['BOT_TOKEN'])
    s3 = S3ContextStore('botanix-context-store')
    m = MainHandler(s3, HelpHandler(bot),
                    StartHandler(bot), RegisterHandler(bot))
    u, uid, epoch = extract(body)
    if u.effective_user is None:
      print(f'No user for update {u}')
    elif u.effective_message is None:
      print(f'No message for update {u}')
    else:
      uid = u.effective_user.id
      message = u.effective_message.text
      try:
        result = await m.handle(uid, message, u)
        if not result.handled:
          await bot.send_message(uid, text='Sorry did not get it.')
          print(result.unhandled_message)
      except Exception as ex:
        traceback.print_exc()
        await bot.send_message(uid, text='There was an error')
        return {
          "statusCode": 200
        }
  except Exception as e:
    traceback.print_exc()
    print(e)
    return {
        "statusCode": 500,
        "body": str(e)
    }


def webhook_handler(event, context):
  loop = asyncio.get_event_loop()
  return loop.run_until_complete(asyncio.gather(do_handle(event, context)))

def extract(body: str) -> (Update, int, int):
  u = Update.de_json(json.loads(body), None)
  uid = None
  epoch = -1
  if u.effective_user is None:
    if u.channel_post is None:
      print(f'WARNING: cannot decipher this: {body}')
      return None, None, None
    else:
      uid = u.channel_post.chat.id
      epoch = u.channel_post.date
  else:
    uid = u.effective_user.id
    epoch = u.message.date

  return u, uid, epoch