# Notifier

![Tests](https://github.com/tristanmsct/Notifier/actions/workflows/tests.yml/badge.svg)
![Coverage](https://raw.githubusercontent.com/tristanmsct/Notifier/master/coverage.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI version](https://badge.fury.io/py/notifier.svg)](https://badge.fury.io/py/notifier)

## Downloading and installing the module

First download the whole thing and unzip it. Then navigate to the package directory. Typically :

`$ cd ~/Downloads/Terminal`

You can use the installer :

`$ ./install`

Or you can paste the "terminal" directory in the site-package of your python installation. The ./install file take care of that and install the package in your current python environment while also install all the dependencies.

## Setting up your slack app

Now you need to set up a slack application that will be able to use the slack API and this interface. You need to start here :

https://api.slack.com/

Create an app and get your two tokens :
```
Bot User OAuth Access Token : "xoxb-XXXX"
OAuth Access Token : "xoxp-XXXX"
```

Now you need to register these two tokens as environment variables like so :
```
BOTAUTH_TOKEN="xoxb-XXXX"
OAUTH_TOKEN="xoxp-XXXX"
```

The second token is used only to clean public channels in slack, so NotifBot can work without it for the most part.

Now you need to grant your app the following permissions :

```
channels:history
channels:read
chat:write
chat:write.public
im:history
im:read
im:write
incoming-webhook
users:read
users:write
```

They are available in the "OAuth & Permissions" your slack application page.

You can give only specific permissions if you want but some features might not work.

## How to use terminal

Content of the `demo.py` file :

```Python
# %% Packages.
from notifbot import NotifBot
import time

# %% Sending messages.

# A single message can be sent using only the notify class method :
NotifBot.notify('Sending a message using the class method.', str_channel='DJ2A424H1')

# But you need to know the exact channl ID.

# It is better to use an instance of NotifBot, which keeps track of all users and public channels, and also
# Allows to manage progress bars.

# To initialize a notifier.
notifier = NotifBot()

# Send a message with the user name :
notifier.notify("Sending a message using the user name.", str_user='Tristan')

# Likewise, the notify instance method can be used to send a message on a public channel.
notifier.notify("Sending a message on a public channel.", str_user='projet')

# Alternatively we can get the channel ID to reuse it everytime, which is simpler when the user name is ambiguous.
str_channel = notifier.get_user_id('Tristan')

# Send a message with the channel ID.
notifier.notify("Sending a message using the channel ID.", str_channel='DJ2A424H1')

# %% Deleting messages.

for i in range(0, 5):
    notifier.notify("Message n{}".format(i), str_channel=str_channel)

# pop_chat delete the last message in the conversation.
notifier.pop_chat(str_channel)

# Or we can use an index (the index is starting from the end).
notifier.pop_chat(str_channel, index=2)
# Here the index 2 was the message n1.

# purge_chat delete all messages in the conversation.
notifier.purge_chat(str_channel)

# To delete message on a public channel, it is a bit more complicated as a bot cannot do it,
# You have to use a user token. If the user token has been provided during the set up (or added after) :
str_channel = notifier.get_user_id('projet')
notifier.purge_chat(str_channel, bl_public=True)

# %% Progress bars

str_channel = notifier.get_user_id('Tristan')

# For now, the progress bar is automatically converted to percentages...
notifier.progress(str_name='spb_1', str_title='Main process', int_total=10, str_channel=str_channel)

# progress_update update the progress bar from its last value
notifier.progress_update('spb_1', int_value=2)
notifier.progress_update('spb_1', int_value=2)
notifier.progress_update('spb_1', int_value=2)

# progress_value set the progress bar to a specific value
notifier.progress_value('spb_1', 3)

# progress_log can be used to keep track of events
notifier.progress_update('spb_1', int_value=2)
notifier.progress_log('spb_1', 'Phase 2', bl_stack_log=True)

notifier.progress_update('spb_1', int_value=2)
notifier.progress_log('spb_1', 'Phase 3', bl_stack_log=True)

# bl_stack_log allows to deleted older logs
notifier.progress_update('spb_1', int_value=3)
notifier.progress_log('spb_1', 'Done', bl_stack_log=False)

# deleting a progress bar
notifier.progress_delete('spb_1')

# %% Example :

notifier.progress('spb_main', 'Main process', 3, str_channel)
for i in range(1, 4):
    notifier.progress_log('spb_main', 'Phase {}'.format(i), bl_stack_log=True)
    notifier.progress('spb_sub{}'.format(i), 'Subprocess n{}'.format(i), 10, str_channel)
    for j in range(0, 10):
        time.sleep(0.1)
        notifier.progress_update('spb_sub{}'.format(i), 1)
    notifier.progress_log('spb_sub{}'.format(i), 'Done', bl_stack_log=False)
    notifier.progress_update('spb_main', 1)
    notifier.progress_delete('spb_sub{}'.format(i))
notifier.progress_value('spb_main', 3)
notifier.progress_log('spb_main', 'Done', bl_stack_log=False)

# notifier.progress_delete('spb_main')
```