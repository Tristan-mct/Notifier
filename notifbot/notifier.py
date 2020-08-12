#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 27 18:02:18 2019.

@author: Tristan Muscat
"""


# =====================================================================================================================
# Import et librairies
# =====================================================================================================================

import requests                                  # Make requests to the slack API.

import numpy as np
import json                                      # Parse the slack API's response.
from fuzzywuzzy import process                   # Find a user with approximate knowledge of their name.
from slack_progress import SlackProgress         # Use a progress bar.

from terminal import InputManager as term        # Input when multiple users have similar names.

import os

# =====================================================================================================================
# Slackbot specific errors.
# =====================================================================================================================


class SlackbotException(Exception):
    """Slackbot erros."""

    def __init__(self, message):
        """Error constructor."""
        super(Exception, self).__init__(message)

# =============================================================================
# Hybrid methods
# =============================================================================


class hybridmethod:
    """Allow to declare a class and instance version of the same method."""

    def __init__(self, fclass, finstance=None, doc=None):
        self.fclass = fclass
        self.finstance = finstance
        self.__doc__ = doc or fclass.__doc__
        # support use on abstract base classes
        self.__isabstractmethod__ = bool(
            getattr(fclass, '__isabstractmethod__', False)
        )

    def classmethod(self, fclass):
        """Class method version of the function."""
        return type(self)(fclass, self.finstance, None)

    def instancemethod(self, finstance):
        """Instance method version of the function."""
        return type(self)(self.fclass, finstance, self.__doc__)

    def __get__(self, instance, cls):
        """Retreive the right version."""
        if instance is None or self.finstance is None:
            # either bound to the class, or no instance method available
            return self.fclass.__get__(cls, None)
        return self.finstance.__get__(instance, cls)

# =====================================================================================================================
# Slack notification interface.
# =====================================================================================================================


class NotifBot:
    """Pour créer un objet de notifications.

    Class Attributes
    ----------------
    str_botauth: str
        Slack Bot Authentification Token. Retreived from environement variables.
    dict_headers: dict
        Simple formatted header used to querry slack API.

    Instance Attributes
    -------------------
    lst_users: list
        A list of all users and associated channels, also public channels. Each user is represented in a dictionnary
        with basic information and the ID used to send a message.
    dict_sbars: dict
        A dictionnary used to store and manage multiple progress bars.
    """

    str_botauth = os.environ['BOTAUTH_TOKEN']
    dict_headers = {
        'Authorization': f'Bearer {str_botauth}',
        'Content-type': 'application/json',
        }

# =====================================================================================================================
# Initialisation.
# =====================================================================================================================

    def __init__(self):
        """Initialize a notifier.

        Creating an instance of a notifier instead of using exclusively class methods allow to keep track of
        progress bars, and also load the list of users and channels only once.
        """
        # Initialisation of the attributes.
        self.dict_users = None
        self.dict_sbars = {}

        # Setting the user list.
        self._set_users()
        self._set_channels()
        self._set_public_channels()

# =====================================================================================================================
# Simple class method to send a message
# =====================================================================================================================

    @hybridmethod
    def notify(cls, str_message, str_channel, str_user=None):
        """Allow to send a message via the slack API.

        This is a classmethod, it can be used to send a one-shot notification. More complex usage should require
        to declare an instance NotifBot. The 'str_user' is here because hybridmethods need to have the same arguments
        for all their versions, but it cannot be used in the class method version.

        Parameters
        ----------
        str_message: str
            The message to send.
        str_channel: str
            The specific ID of the channel where to send the message.
        str_user: str
            Not in use in this version of the function. Default is None.
        """
        data = f'{{"channel":"{str_channel}", "text":"{str_message}"}}'
        requests.post('https://slack.com/api/chat.postMessage', headers=NotifBot.dict_headers, data=data)

# =====================================================================================================================
# Setters / Getters
# =====================================================================================================================

    def _set_users(self):
        """Initialize the list of users."""
        # Getting the users.list from slack API and parsing the result.
        response = requests.post('https://slack.com/api/users.list', headers=NotifBot.dict_headers)
        res = json.loads(response.content.decode("utf-8"))['members']

        # Storing all important information in a list of dictionnaries.
        self.lst_users =\
            [{'ID': elt['id'], 'Team_ID': elt['team_id'], 'Name': elt['name'],
              'Real_name': elt['real_name'], 'Channel': np.nan}
             if 'real_name' in elt.keys()
             else {'ID': elt['id'], 'Team_ID': elt['team_id'], 'Name': elt['name'],
                   'Real_name': np.nan, 'Channel': np.nan}
             for elt in res]

    def _set_channels(self):
        """Add, for each user, the channel to send them messages."""
        # Getting the im.list from the slack API and parsing the result.
        response = requests.post('https://slack.com/api/im.list', headers=NotifBot.dict_headers)
        res = json.loads(response.content.decode("utf-8"))['ims']

        lst_channels = [{'ID': elt['user'], 'Channel': elt['id']} for elt in res]

        # For each channel, we look up a user with the same ID, when their is a match, the channel is set
        # in the list of users.
        for channel in lst_channels:
            for user in self.lst_users:
                if user['ID'] == channel['ID']:
                    user['Channel'] = channel['Channel']

    def _set_public_channels(self):
        """Add every public channel."""
        # Getting the channels.list from the slack API and parsing the result.
        response = requests.post('https://slack.com/api/channels.list', headers=NotifBot.dict_headers)
        res = json.loads(response.content.decode("utf-8"))['channels']

        # Storgin everything in a dictionnary.
        lst_public_channels =\
            [{'ID': elt['created'], 'Name': elt['name_normalized'],
              'Real_name': elt['name'], 'Channel': elt['id']}
             for elt in res]

        # The dictionnary is added to the list of users, the keys to search and to get a channel ID are the same.
        self.lst_users = self.lst_users + lst_public_channels

# =====================================================================================================================
# Getting channels and messages
# =====================================================================================================================

    def get_list_messages(self, str_channel=None, str_user=None, bl_public=False):
        """Retreive the list of messages on a channel. Used mostly to purge a channel.

        Parameters
        ----------
        str_channel : str, optional
            The channel ID. The default is None.
        str_user : str, optional
            The name of the user. The default is None.
        bl_public: boolean
            Is the channel public or not.

        Returns
        -------
        dict_messages : dict
            A dictionnary with every message in the channel.
        """
        # If a channel ID is not provided, we use the user name to get a channel ID.
        if str_channel is None:
            str_channel = self.get_user_id(str_user)

        # Retreiving the messages with slack API.
        if bl_public:
            # This token is not a class variable so the user has the choice not to use it.
            str_token = os.environ['OAUTH_TOKEN']
        else:
            str_token = NotifBot.str_botauth
        response =\
            requests.post(f'https://slack.com/api/conversations.history?token={str_token}&channel={str_channel}')
        dict_messages = json.loads(response.content.decode("utf-8"))['messages']

        return dict_messages

    def get_user_id(self, str_user):
        """Get a user's ID from their name.

        Parameters
        ----------
        str_user : str
            The user's name.

        Returns
        -------
        str_channel : str
            The channel ID associated to the user.
        """
        # We search trough the user list with fuzzysearch, retreiving several possible matchs.
        lst_user_names = [elt['Real_name'] for elt in self.lst_users if isinstance(elt['Real_name'], str)]
        lst_best_names = process.extractBests(str_user, lst_user_names, score_cutoff=80)

        # If we get more than one match, the user is prompted to pick the right one.
        if len(lst_best_names) > 1:
            print(f'Serveral match for the name {str_user}.')
            for i in range(0, len(lst_best_names)):
                print(f'{str(i + 1)} : {lst_best_names[i][0]}')
            print(f'{str(i + 2)} : Quit')
            index_name = term.force_read(term.read_numeric, 'Your pick : ', True, 1, len(lst_best_names) + 1)
            if index_name == (i + 2):
                raise SlackbotException('No match for {} user.'.format(str_user))
            str_user = lst_best_names[index_name - 1][0]
        # If their is only one match, then we get their channel ID.
        elif len(lst_best_names) == 1:
            str_user = lst_best_names[0][0]
        # If no match, then error.
        else:
            raise SlackbotException(f'No match for {str_user} user.')

        # Looking up the channel ID in the user list.
        str_channel = [elt['Channel'] for elt in self.lst_users if elt['Real_name'] == str_user][0]

        # If the user exist but no channel is open with them.
        if not isinstance(str_channel, str):
            raise SlackbotException(f'No channel openned with {str_user}.')

        return str_channel

# =====================================================================================================================
# Sending and deleting messages
# =====================================================================================================================

    @notify.instancemethod
    def notify(self, str_message: str, str_channel=None, str_user=None):
        """Send a message to a user or on a channel.

        Parameters
        ----------
        str_message: str
            The message to send.
        str_channel: str
            The ID of the user or the public channel.
        str_user : str
            If the channel ID is unknown then the user's name can be used to get it.
        """
        # If the channel ID is unknown then the user's name can be used to get it.
        if str_channel is None:
            str_channel = self.get_user_id(str_user)

        # Send a message through the slack API.
        data = f'{{"channel":"{str_channel}", "text":"{str_message}"}}'
        requests.post('https://slack.com/api/chat.postMessage', headers=NotifBot.dict_headers, data=data)

    def progress(self, str_name, str_title, int_total, str_channel=None, str_user=None):
        """Create a progress bar.

        Parameters
        ----------
        str_name: str
            The name of the progress bar. Used to reference it once created.
        str_title: str
            The displayed title of the progress bar.
        str_channel: str
            The ID of the user or the public channel.
        str_user : str
            If the channel ID is unknown then the user's name can be used to get it.
        """
        # If the channel ID is unknown then the user's name can be used to get it.
        if str_channel is None:
            str_channel = self.get_user_id(str_user)

        # Adding the progress bar with it's title and total.
        progress_bar = SlackProgress(NotifBot.str_botauth, str_channel)
        self.dict_sbars[str_name] = {'pbar': progress_bar.new(total=int_total), 'title': str_title}
        self.dict_sbars[str_name]['pbar'].log(str_title)

    def progress_set_title(self, str_name, str_title):
        """Set the progress bar title. Used mostly to change it.

        Parameters
        ----------
        str_name: str
            The name of the progress bar. Used to reference it once created.
        str_title: str
            The displayed title of the progress bar.
        """
        self.dict_sbars[str_name]['title'] = str_title

    def progress_update(self, str_name, int_value):
        """Update a prgress bar.

        Parameters
        ----------
        str_name: str
            The name of the progress bar. Used to reference it once created.
        int_value: int
            The value to add.
        """
        self.dict_sbars[str_name]['pbar'].pos =\
            round((self.dict_sbars[str_name]['pbar'].pos +
                   (int_value * 100 / self.dict_sbars[str_name]['pbar'].total)), 2)

    def progress_value(self, str_name, int_value):
        """Set the progress bar to a specific value.

        Parameters
        ----------
        str_name: str
            The name of the progress bar.
        int_value: int
            The value where to set the progress bar.
        """
        self.dict_sbars[str_name]['pbar'].pos =\
            round((int_value * 100 / self.dict_sbars[str_name]['pbar'].total), 2)

    def progress_log(self, str_name, str_log, bl_stack_log=True):
        """Log an event into the progress bar (display under the title in slack).

        Parameters
        ----------
        str_name: str
            The name of the progress bar.
        str_log : str
            The message to log.
        bl_stack_log: bool
            Should we erease all previous logged messages.
        """
        # The message is added to the progress bar.
        self.dict_sbars[str_name]['pbar'].log(f"{self.dict_sbars[str_name]['title']} - {str_log}")

        # If we decide so, every logged message added before the new one is deleted.
        if not bl_stack_log:
            self.dict_sbars[str_name]['pbar']._msg_log = [self.dict_sbars[str_name]['pbar']._msg_log[-1]]
            self.dict_sbars[str_name]['pbar']._update()

    def progress_delete(self, str_name):
        """Delete a progress bar.

        Parameters
        ----------
        str_name: str
            The name of the progress bar.
        """
        # In order to delete a message (a progress bar in this case), we need its time stamp
        str_ts = self.dict_sbars[str_name]['pbar'].msg_ts
        data = f"""{{"channel":"{self.dict_sbars[str_name]['pbar'].channel_id}", "ts":"{str_ts}"}}"""
        requests.post('https://slack.com/api/chat.delete', headers=NotifBot.dict_headers, data=data)

    def purge_chat(self, str_channel=None, str_user=None, bl_public=False):
        """Purge an entier chat.

        Parameters
        ----------
        str_channel: str
            The ID of the user or the public channel.
        str_user : str
            If the channel ID is unknown then the user's name can be used to get it.
        bl_public: boolean
            Is the channel public or not.
        """
        # If the channel ID is unknown then the user's name can be used to get it.
        if str_channel is None:
            str_channel = self.get_user_id(str_user)

        # Getting the list of all message on the channel.
        lst_messages = self.get_list_messages(str_channel, bl_public=bl_public)

        # For each message, we use its time stamp to delete it.
        for message in lst_messages:
            str_ts = message['ts']
            data = '{"channel":"' + str_channel + '", "ts":"' + str_ts + '"}'
            requests.post('https://slack.com/api/chat.delete', headers=NotifBot.dict_headers, data=data)

    def pop_chat(self, str_channel=None, str_user=None, index=0, bl_public=False):
        """Delete one message by index.

        Parameters
        ----------
        str_channel: str
            The ID of the user or the public channel.
        str_user : str
            If the channel ID is unknown then the user's name can be used to get it.
        index: int
            The index of the message to delete (starting at the latest).
        bl_public: boolean
            Is the channel public or not.
        """
        # If the channel ID is unknown then the user's name can be used to get it.
        if str_channel is None:
            str_channel = self.get_user_id(str_user)

        # Getting the list of all message on the channel.
        lst_messages = self.get_list_messages(str_channel, bl_public=bl_public)

        # To delete a specific message, we need its time stamp.
        str_ts = lst_messages[index]['ts']
        data = '{"channel":"' + str_channel + '", "ts":"' + str_ts + '"}'
        requests.post('https://slack.com/api/chat.delete', headers=NotifBot.dict_headers, data=data)
