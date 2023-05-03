# botanix
**A Telegram bot mini-framework for handling the workflow**

## Why may I need botanix
Developing [Telegram bots](https://core.telegram.org/bots/api) is fairly easy: all that it requires is to set up a webhook to receive messages (`update`s) from users and respond to them. The messages, however, are stateless and the bot itself is meant to maintain the state and track where each user has been in its interaction in order to be able to route the message to the correct handler and navigate the user through the workflow. Without a simple framework, the code quickly turns into a mess. 

**botanix** makes it easy for Telegram bot developers to define the workflow of their python bots in code according to simple conventions (essentially "declare" the workflow) and Botanix wires up the workflow and sends the messages to the right handler.

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
    store = DdbStore()
    bot = Bot(bot_token)
    
    # create MainHandler with instances of all handlers
    m = MainHandler(store, RegisterHandler(bot), ...)    
    result = m.handle(uid, message, update)

    # based on result interact
```


## Concepts

### Tracks and steps
The workflow contains two main concepts: *Tracks* and *Steps*. A track is made of steps (zero-based) and represents a top level functionality of the bot, e.g. Help (typically triggered by `/help` command) or Register, etc. Once in a track, the user navigates through various steps of the workflow until it completes or abandons the track.

In botanix, a track is represented by a class, inherited from `BaseHandler`. For example, registration track typically started by receiving `/register` command is by convention implemented in a class named `RegisterHandler`.

```python
class RegisterHandler(BaseHandler):
  pass
```

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

Name of the method needs to have zero-based `_<step number>` as a suffix. This method will handle the first step:

```python
def registration_step_0(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
  pass
```

Alternatively, you can use `@step_number` decorator to achieve the same thing:

```python
@step_number(0)
def start_registration(self, command: str, update: Update, context: HandlingContext) -> HandlingResult:
  pass
```

It is possible to have more than one method for a step in which case, following a [Chain-of-responsibility pattern](https://en.wikipedia.org/wiki/Chain-of-responsibility_pattern), the methods will be called in succession until one of them successfully handles the update, and it will then short-circuit and return. Ordering of the calls cannot be guaranteed and is controlled by the order python's `inspect` operates.

### HandlingResult
After receiving an update, a handler method could signal back as below:

#### 1) Successful handling
It handles the update, sends appropriate actions (typically via `Bot` object) and then returns a *handled* result:

```python
return HandlingResult.success_result()
```

This is simply a shortcut for creating an instance of `HandlingResult` and setting appropriate attributes needed to signal successful handling.

#### 2) Successful handling and closing the track
It handles the update, sends appropriate actions (typically via `Bot` object) and then returns a *terminal* result:

```python
return HandlingResult.terminal_result()
```

#### 3) Successful handling but changing the next step
It handles the update but overrides what the next the step would be (typically it would be `current_step+1`). This could be handy to shortcut to higher steps missing unnecessary steps or sending back to start, etc.

```python
return HandlingResult.override_step_result(3)
```

#### 4) Successful handling but changing the track
It handles the update but totally changes the current track starting from step 0 (or any other step)

```python
return HandlingResult.new_track_name('SomeOtherTrack', new_step=42)

```

#### 5) Unsuccessful handling
The method is unable to handle (most likely due to bad user input). In this case, the user stays at the same track and the same step.

```python
return HandlingResult.unhandled_result('Input is invalid. Please try again')

```

### Context
As discussed, the webhook receiving the messages is completely stateless and piecing together and making sense of where a user is in its journey poses the main challenge for otherwise simple request-response paradigm of a Telegram bot. 

`botanix` introduces a simple bag as the `HandlingContext` which is responsible to keep track of where a user is in its journey. More importantly, it allows a simple means to store user input as the user moves through subsequent steps, e.g. filling a multi-field form in each step.


#### Persistence
The context, for all but the most trivial use cases, must be persisted: the store must implement `BaseContextStore`. `botanix` supplies an in-memory storage for test purpose but you can simply implement persistence over any key-value store (Redis, DynamoDb, traditional RDBMS, NATS KV, etc). The key is always Telegram's User ID, namely `uid`.

These persistence stores will be provided as separate python packages.

## Wire-up: MainHandler
As demonstrated in the example above, the webhook receives the Update in the persisted format. In `botanix`, responsibility of brokering Telegram messages a.k.a "updates" to your handler classes inherited from `BaseHandler`. 

`MainHandler` is instantiated by providing a context persistence store along with all your handler classes passed as instances.

```python
m = MainHandler(store, RegisterHandler(bot), HelpHandler(bot), ...)
```

Upon receiving the update from Telegram in your webhook, extract User ID and message of the text and pass to to your MainHandler instance:

```python
result = m.handle(uid, message, update)
```

Considering this call can raise error, you need to do it in a `try` block. Once a result is returned, check for if it is handled

```python
  try:
    result = m.handle(uid, message, u)
    if not result.handled:
      bot.send_message(uid, text='Sorry did not get it.')
  except Exception as ex:
    traceback.print_exc()
    bot.send_message(uid, text='There was an error. Please try again.')
```

### Special Handlers: StartHandler and HelpHandler
`botanix` considers Help and Start as generic handlers and treats them slightly differently in the sense that the updates that have `/start` or `/help` will be treated as calling them even if the user is midway in an established track. This means that if, for example, your `RegisterHandler` asks user's name and in response, the user types `/start`, then this message will not be received by that handler but by your `StartHandler`.

This behaviour is governed by `MainHandler.generic_handler_names` which has the value `['help', 'start']`. You can change this behaviour by setting it to `[]` but typically you are meant to create `StartHandler` and `HelpHandler` and this behaviour is desirable since it provides a short-circuit to start again or see the help output.

