#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 27 18:02:18 2019.

@author: tristan
"""


# =====================================================================================================================
# Import et librairies
# =====================================================================================================================

import requests                                  # Pour interroger l'API slack.
import json                                      # Traitement des réponses de l'API slack.
from fuzzywuzzy import process                   # Pour chercher une personne dans la liste des utilisateurs.
import numpy as np

from slack_progress import SlackProgress         # Pour afficher une barre d'avancement sur slack.
import socket                                    # Pour verifier si internet est on.
from socket import gaierror

from .tools.Terminal import InputManager as term

# =============================================================================
# Erreurs spécifique au slack bot.
# =============================================================================


class SlackbotException(Exception):
    """Les erreurs du slackbot."""

    def __init__(self, message):
        """Constructeur de l'erreur."""
        super(Exception, self).__init__(message)

# =====================================================================================================================
# Module d'envoi de notifications slack.
# =====================================================================================================================


class slack_notifications:
    """Pour créer un objet de notifications.

    Attributes
    ----------
    str_token: str
        Le token d'authentification du 'bot'. Avec la nouvelle API, le bot est directement rattaché à un utilisateur,
        c'est pourquoi il est fixe. A voir comment ça évolue dans le futur.
    dict_headers: dict
        Un dictionnaire contenant les headers nécessaire pour utiliser l'API slack.
    dict_users: dict
        Le dictionnaire qui contient l'ensemble des utilisateurs avec le channel qui correspond à chacun.
    slack_progress:
        Un objet permettant d'initialiser des progress bars sur slack.
    dict_sbars: dict
        Un dictionnaire de progress bars nominative qui permet d'en gérer plusieurs à la foi.

    """

# =====================================================================================================================
# Initialisation.
# =====================================================================================================================

    def __init__(self, bl_sec_internet=False):
        """Fonction d'intialisation du notifier.

        Le notifier s'initialise vide, puisque le token permet de récuperer toutes les informations nécessaires
        et celui-ci est fixe.

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        """
        if self.internet_on():
            # Initialisation des attributs.
            self.str_token = ''
            self.dict_headers = None
            self.dict_users = None
            self.slack_progress = None
            self.dict_sbars = {}
            self.bl_sec_internet = bl_sec_internet

            # On set le header et la table des utilisateurs.
            self._set_headers()
            self._set_users()
            self._set_channels()
        else:
            raise SlackbotException('Erreur de connexion.')

# =====================================================================================================================
# Setters / Getters
# =====================================================================================================================

    def _set_headers(self):
        """Fonction d'intialisation du header.

        Le header s'initialise simplement avec le token, pas besoin de plus pour le moment.

        """
        self.dict_headers = {
            'Authorization': 'Bearer {}'.format(self.str_token),
            'Content-type': 'application/json',
            }

    def _set_users(self):
        """Fonction d'initialisation de la table des utilisateurs.

        On récupère la table des utilisateurs avec leurs informations de base.

        """
        # On récupère la users.list et on parse le résultat, puis on range le tout dans un dictionnaire
        response = requests.post('https://slack.com/api/users.list', headers=self.dict_headers)
        res = json.loads(response.content.decode("utf-8"))['members']

        # On range tout dans un bon vieux dict.
        self.lst_users =\
            [{'ID': elt['id'], 'Team_ID': elt['team_id'], 'Name': elt['name'],
              'Real_name': elt['real_name'], 'Channel': np.nan}
             if 'real_name' in elt.keys()
             else {'ID': elt['id'], 'Team_ID': elt['team_id'], 'Name': elt['name'],
                   'Real_name': np.nan, 'Channel': np.nan}
             for elt in res]

    def _set_channels(self):
        """Fonctio d'ajout des channels à la table des utilisateurs.

        Pour chaque utilisateur, on ajoute l'ID du channel, car c'est ce qui est utilisé pour intéragir avec slack.

        """
        # On récupère la liste des "im" (Instant Messages) de l'utilisateur.
        response = requests.post('https://slack.com/api/im.list', headers=self.dict_headers)
        res = json.loads(response.content.decode("utf-8"))['ims']

        lst_channels = [{'ID': elt['user'], 'Channel': elt['id']} for elt in res]

        # /!\ On ajoute les channel IDs au df_users cependant, les ID pour les utilisateurs avec qui on n'a jamais
        # parlé n'existe pas ! il faut donc envoyer au moins un premier message depuis l'application.
        for channel in lst_channels:
            for user in self.lst_users:
                if user['ID'] == channel['ID']:
                    user['Channel'] = channel['Channel']

# =====================================================================================================================
# Récuperation chaînes et messages
# =====================================================================================================================

    def get_list_messages(self, str_channel=None, str_user=None):
        """Fonction pour obtenir la liste des messages envoyés à un utilisateur.

        Parameters
        ----------
        str_channel : str, optional
            L'ID du channel. The default is None.
        str_user : str, optional
            Le nom de l'utilisateur. The default is None.

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        Returns
        -------
        dict_messages : dict
            La liste des messages, dans un dictionnaire.

        """
        if self.internet_on(self.bl_sec_internet):
            # Si l'ID du channel n'est pas connu, on le récupère à partir du nom de l'utilisateur.
            if str_channel is None:
                str_channel = self.get_user_id(str_user)

            # l'appel à l'API classique ne fonctionne pas, je ne sais pas pourquoi alors on utilise directement l'URL.
            response = requests.post('https://slack.com/api/conversations.history?token={}&channel={}'.
                                     format(self.str_token, str_channel))
            dict_messages = json.loads(response.content.decode("utf-8"))['messages']
        else:
            raise SlackbotException('Erreur de connexion.')

        return dict_messages

    def get_user_id(self, str_user):
        """Fonction d'obtention de l'ID du channel d'un user à partir de son nom.

        Parameters
        ----------
        str_user : str
            Le nom de l'utilisateur.

        Raises
        ------
        SlackbotException
            Si le nom demandé ne correspond à rien dans la base.

        Returns
        -------
        str
            L'ID du channel lié à l'utilisateur.

        """
        # On cherche le nom de l'utilisateur dans la liste des noms grâce à un "fuzzy search".
        lst_user_names = [elt['Real_name'] for elt in self.lst_users if isinstance(elt['Real_name'], str)]
        lst_best_names = process.extractBests(str_user, lst_user_names, score_cutoff=80)

        # Si on a plus qu'un nom qui correspond alors on demande un choix.
        if len(lst_best_names) > 1:
            print("Plusieurs noms correspondent à {}.".format(lst_best_names))
            for i in range(0, len(lst_best_names)):
                print('{} : {}'.format(str(i + 1), lst_best_names[i][0]))
            print('{} : Quitter'.format(str(i + 2)))
            index_name = term.force_read(term.read_numeric, "Choix : ", True, 1, len(lst_best_names) + 1)
            if index_name == (i + 2):
                raise SlackbotException('No match for {} user.'.format(str_user))
            str_user = lst_best_names[index_name - 1][0]
        # Si il n'y a qu'un nom alors on considère que c'est le bon.
        elif len(lst_best_names) == 1:
            str_user = lst_best_names[0][0]
        # Si aucun nom n'est trouvé, alors ça plante.
        else:
            raise SlackbotException('No match for {} user.'.format(str_user))

        # On retourne l'ID du channel.
        str_channel = [elt['Channel'] for elt in self.lst_users if elt['Real_name'] == str_user][0]

        if not isinstance(str_channel, str):
            raise SlackbotException("Aucune conversation n'existe avec {}.".format(str_user))

        return str_channel

# =====================================================================================================================
# Envoi et suppression de messages
# =====================================================================================================================

    def notify(self, str_message, str_channel=None, str_user=None):
        """Fonction d'envoie d'un message à un utilisateur.

        Parameters
        ----------
        str_message: str
            Le message à envoyer.
        str_channel: str
            L'ID du channel ou envoyer le message.
        str_user : str
            Le nom de l'utilisateur à qui envoyer le message, si on a pas son ID.

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        """
        if self.internet_on(self.bl_sec_internet):
            # Si l'ID du channel n'est pas connu, on le récupère à partir du nom de l'utilisateur.
            if str_channel is None:
                str_channel = self.get_user_id(str_user)

            # On construit la requette et on envoie le message.
            data = '{"channel":"' + str_channel + '", "text":"' + str_message + '"}'
            requests.post('https://slack.com/api/chat.postMessage', headers=self.dict_headers, data=data)
        else:
            raise SlackbotException('Erreur de connexion.')

    def progress(self, str_name, str_title, int_total, str_channel=None, str_user=None):
        """Fonction d'envoie d'un message à un utilisateur.

        Parameters
        ----------
        str_name: str
            Le nom de la progress bar.
        str_title: str
            Le titre de la progress bar (celui qui est affiché dans slack).
        str_channel: str
            L'ID du channel ou envoyer le message.
        str_user : str
            Le nom de l'utilisateur à qui envoyer le message, si on a pas son ID.

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        """
        if self.internet_on(self.bl_sec_internet):
            # Si l'ID du channel n'est pas connu, on le récupère à partir du nom de l'utilisateur.
            if str_channel is None:
                str_channel = self.get_user_id(str_user)

            # On ajoute la progress bar, avec son nom et son total.
            self.slack_progress = SlackProgress(self.str_token, str_channel)
            self.dict_sbars[str_name] = {'pbar': self.slack_progress.new(total=int_total), 'title': str_title}
            self.dict_sbars[str_name]['pbar'].log(str_title)
        else:
            raise SlackbotException('Erreur de connexion.')

    def progress_set_title(self, str_name, str_title):
        """Fonction de set du titre de la progress bar.

        Parameters
        ----------
        str_name: str
            Le nom de la progress bar.
        str_title: str
            Le nouveau titre de la progress bar (celui qui est affiché dans slack).

        """
        self.dict_sbars[str_name]['title'] = str_title

    def progress_update(self, str_name, int_value):
        """Fonction d'update d'une progress bar.

        Parameters
        ----------
        str_name : str
            Le nom de la progress bar (il s'agit du nom affiché et du nom par lequel il est référencé).
        int_value : int
            La valeur à ajouter.

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        """
        if self.internet_on(self.bl_sec_internet):
            self.dict_sbars[str_name]['pbar'].pos = round((self.dict_sbars[str_name]['pbar'].pos
                                                           + (int_value * 100
                                                              / self.dict_sbars[str_name]['pbar'].total)), 2)
        else:
            raise SlackbotException('Erreur de connexion.')

    def progress_value(self, str_name, int_value):
        """Fonction de set de la valeur d'une progress bar.

        Parameters
        ----------
        str_name : str
            Le nom de la progress bar (il s'agit du nom affiché et du nom par lequel il est référencé).
        int_value : int
            La valeur à set.

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        """
        if self.internet_on(self.bl_sec_internet):
            self.dict_sbars[str_name]['pbar'].pos = round((int_value * 100
                                                           / self.dict_sbars[str_name]['pbar'].total), 2)
        else:
            raise SlackbotException('Erreur de connexion.')

    def progress_log(self, str_name, str_log, bl_stack_log=True):
        """Fonction de log d'un evenement sur une progress bar.

        Parameters
        ----------
        str_name : str
            Le nom de la progress bar (il s'agit du nom affiché et du nom par lequel il est référencé).
        str_log : str
            Le message à logger.
        bl_stack_log: bool
            Indique si on doit effacer les log precedent sur cette progress bar.

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        """
        if self.internet_on(self.bl_sec_internet):
            # On ajoute le message à la progress bar.
            self.dict_sbars[str_name]['pbar'].log("{} - {}".format(self.dict_sbars[str_name]['title'], str_log))

            # Si on le décide, on supprime les messages loggés avant.
            if not bl_stack_log:
                self.dict_sbars[str_name]['pbar']._msg_log = [self.dict_sbars[str_name]['pbar']._msg_log[-1]]
                self.dict_sbars[str_name]['pbar']._update()
        else:
            raise SlackbotException('Erreur de connexion.')

    def progress_delete(self, str_name):
        """Fonction de suppression d'une progress bar.

        Parameters
        ----------
        str_name : str
            Le nom de la progress bar à supprimer.

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        """
        if self.internet_on(self.bl_sec_internet):
            # Pour supprimer une progress bar, il faut récuperer son time stamp
            str_ts = self.dict_sbars[str_name]['pbar'].msg_ts
            data = '{"channel":"' + self.dict_sbars[str_name]['pbar'].channel_id + '", "ts":"' + str_ts + '"}'
            requests.post('https://slack.com/api/chat.delete', headers=self.dict_headers, data=data)
        else:
            raise SlackbotException('Erreur de connexion.')

    def purge_chat(self, str_channel=None, str_user=None):
        """Fonction de purge d'un chat.

        Parameters
        ----------
        str_channel: str
            L'ID du channel ou envoyer le message.
        str_user : str
            Le nom de l'utilisateur à qui envoyer le message, si on a pas son ID.

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        """
        if self.internet_on(self.bl_sec_internet):
            # Si l'ID du channel n'est pas connu, on le récupère à partir du nom de l'utilisateur.
            if str_channel is None:
                str_channel = self.get_user_id(str_user)

            # On récupère la liste des messages pour le channel donné.
            lst_messages = self.get_list_messages(str_channel)

            # Pour chaque message, on utilise son time stamp pour le supprimer.
            for message in lst_messages:
                str_ts = message['ts']
                data = '{"channel":"' + str_channel + '", "ts":"' + str_ts + '"}'
                requests.post('https://slack.com/api/chat.delete', headers=self.dict_headers, data=data)
        else:
            raise SlackbotException('Erreur de connexion.')

    def pop_chat(self, str_channel=None, str_user=None, index=0):
        """Fonction de suppression d'un message unique.

        Parameters
        ----------
        str_channel: str
            L'ID du channel ou envoyer le message.
        str_user : str
            Le nom de l'utilisateur à qui envoyer le message, si on a pas son ID.
        index: int
            L'index du message à supprimer (en partant de la fin).

        Raises
        ------
        SlackbotException
            cette étape ne peut pas fonctionner sans internet.

        """
        if self.internet_on(self.bl_sec_internet):
            # Si l'ID du channel n'est pas connu, on le récupère à partir du nom de l'utilisateur.
            if str_channel is None:
                str_channel = self.get_user_id(str_user)

            # On récupère la liste des messages pour le channel donné.
            lst_messages = self.get_list_messages(str_channel)

            # Pour récupère le time stamp du message à supprimer et on le supprimer.
            str_ts = lst_messages[index]['ts']
            data = '{"channel":"' + str_channel + '", "ts":"' + str_ts + '"}'
            requests.post('https://slack.com/api/chat.delete', headers=self.dict_headers, data=data)
        else:
            raise SlackbotException('Erreur de connexion.')

# =====================================================================================================================
# Envoi de message sans passer par un objet
# =====================================================================================================================

    @staticmethod
    def internet_on(bl_sec_internet=True):
        """Methode qui verifie si une connexion a internet existe ou non."""
        if bl_sec_internet:
            bl_internet_is_on = False
            try:
                # Connexion à l'hôte
                socket.create_connection(("www.google.com", 80))
                bl_internet_is_on = True
            except ConnectionError:
                bl_internet_is_on = False
            except gaierror:
                bl_internet_is_on = False

            return bl_internet_is_on
        else:
            return True

# Dissocier le titre et le nom de la barre