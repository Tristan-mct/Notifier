#!/usr/bin/env python3
"""
Created on Tue Aug 11 11:50:14 2020

@author: Tristan Muscat
"""
import unittest  # For unit testing
from unittest.mock import patch

from notifbot import NotifBot


class TestNotifbot(unittest.TestCase):

    def test_readline(self):
        notifier = NotifBot()
        str_channel = notifier.get_user_id('Tristan')
        self.assertEqual(str_channel, "D02JZP30F0U")




if __name__ == "__main__":
    unittest.main()
