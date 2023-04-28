# botanix
**A Telegram bot mini-framework for handling the workflow**

## Why may I need botanix
Developing [Telegram bots](https://core.telegram.org/bots/api) is fairly easy: all that it requires is to set up a web hook to receive messages (`update`s) from users and respond to them. The messages, however, are stateless and the bot itself is meant to maintain the state and track where each user has been in its interaction in order to be able to route the message to the correct handler and navigate the user through the workflow. Without a simple framework, the code quickly turns into a mess. 

**Botanix** makes it easy for Telegram bot developers to define the workflow of their python bots in code according to simple conventions (essentially "declare" the workflow) and Botanix wires up the workflow and sends the messages to the right handler.

## Getting started
To install, use pip:

``` bash
pip install botanix
```

And import botanix and create your first Handler, inheriting from `BaseHandler`:

```python
from telegram import Bot, Update
from botanix.handling import BaseHandler, HandlingResult, HandlingContext

# By convention, this class will handle /register track
class RegisterHandler(BaseHandler):
    def __init__(self, bot: Bot):
        self.bot = bot
    
    # note "_0" suffix signifying the first step of the track 
    def registeration_step_0(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
        # use self.bot to send messages to user
        ... 
        # and then tell botanix message was successfully handled hence to move to the next step
        return HandlingResult.success_result()
    def registeration_step_1(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
        # use user input to do the work necessary
        ...
        # use self.bot to send messages to user
        ... 
        # and then tell botanix message was successfully handled and end the track
        return HandlingResult.terminal_result()
    
```
And then create a `MainHandler` and use it in your Telegram webhook (this case, a Lambda function):

```python
def get_update(event, context):
  
    body = event['body']
    
    # extract from the webhook payload
    update, uid, epoch = helper_function.extract(body)
    message = update.effective_message.text
    
    # DynamoDB-based repo for storing context
    repo = DdbRepo()
    bot = Bot(bot_token)
    
    # create MainHandler with instances of all handlers
    m = MainHandler(repo, RegisterHandler(bot), ...)    
    result = m.handle(uid, message, update)

    # based on result interact
```


## Concepts

### Tracks and steps
The workflow contains two main concepts: *Tracks* and *Steps*. A track is made of steps (zero-based) and represents a top level functionality of the bot, e.g. Help (typically triggered by `/help` command) or Register, etc. Once in a track, the user navigates through various steps of the workflow until it completes or abandons the track.

In botanix, a track is represented by a class. For example, registration track typically started by receiving `/register` command is by convention implemented in a class named `RegisterHandler`.

If you do not want to stick to the convention, you can define the track name using the `@track_name` decorator:

```python
from botanix.handling import BaseHandler, track_name

@track_name('Register')
class LookMaNoConvention(BaseHandler):
  pass
```

Within a track, represented by a class, each step is implemented as a method with this signature:

```python
    method_<step number>(self, command: str, update: Update, context: HandlingContext) -> HandlingResult
```

Name of the needs to have zero-based `_<step number>` as a suffix. This method will handle the first step:

```python
def registeration_step_0(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
  pass
```




