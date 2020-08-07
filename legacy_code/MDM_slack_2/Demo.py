#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 17:52:53 2020.

@author: tristan
"""

# Packages
from MDMBot import notifications as nf

# Faut utiliser ça sinon l'API slack marche pas
import nest_asyncio
nest_asyncio.apply()

# Pour initialiser un notifier
notifier = nf.slack_notifications('param_notifs.yaml', 'MDM-Bot')

# Message à une personne
notifier.notify("Hello", str_user='Tristan')

# Si il y a plusieurs personnes pour le même nom alors on prompt un choix
notifier.notify("Hello", str_user='David')

# Message dans un groupe
notifier.notify("Message de groupe", str_channel='events')

# Message privé à une personne dans un groupe
notifier.notify("Message Ephémère", str_channel='events', str_user='Tristan')

# TQDM
notifier.init_sbar(total=100, str_user='trist')
for i in range(0, 101):
    notifier.sbar_set(i)

notifier.notify('Prout', str_user='trist')
