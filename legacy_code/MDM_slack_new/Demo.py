#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:52:53 2020.

@author: tristan
"""

# Packages
from MDMBot import notifications as nf
import time

# Faut utiliser ça sinon l'API slack marche pas
import nest_asyncio
nest_asyncio.apply()

# Pour initialiser un notifier
notifier = nf.slack_notifications()

# Message à une personne
notifier.notify("Hello", str_user='Tristan')

for i in range(0, 5):
    notifier.notify(f'Message n{i}', str_user='Tristan')

notifier.pop_chat(str_user='Tristan')

notifier.purge_chat(str_user='Tristan')

notifier.progress('sbar_test', 'Barre de chargement.', 10, str_user='Tristan')
for i in range(0, 10):
    time.sleep(1)
    notifier.progress_update('sbar_test', 1)

notifier.progress_value('sbar_test', 5)
notifier.progress_log('sbar_test', 'message')
notifier.progress_delete('sbar_test')

notifier.purge_chat(str_user='Tristan')
