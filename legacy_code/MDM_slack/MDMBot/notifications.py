#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 27 18:02:18 2019.

@author: tristan
"""


# =====================================================================================================================
# Import et librairies
# =====================================================================================================================


import slack                                     # Pour envoyer des notifications par slack

from slack_progress import SlackProgress         # Pour afficher une bar d'avancement sur slack
import socket                                    # Pour verifier si internet est on

from .tools.Terminal import InputManager as term
from fuzzywuzzy import process

from .conf.conf_bot import TOKEN_BOT, TOKEN_USER

# Commandes :
# python -m pip install --user slackbot
# pip install slackclient


# =====================================================================================================================
# Module d'envoi de notifications slack
# =====================================================================================================================


class slack_notifications:
    """Pour créer un objet de notifications."""

# =====================================================================================================================
# Initialisation
# =====================================================================================================================

    def __init__(self, str_path, str_token):
        """Fonction d'initialisation du notifieur slack.

        Parameters
        ----------
        str_path : str
            le chemin du fichier contenant les parametres de notifications.
        str_token : str
            le nom du bot pour lequel recuperer les tokens.
        """
        # Toujours la même chose à priori, pour le moment
        self.headers = {'Content-type': 'application/json'}
        # Si il est connu il est set ici, sinon set à None
        self.str_token_bot = None
        self.str_token_user = None
        self.sc_bot = None
        self.sc_user = None
        self.sp = None
        self.sbar = None

        # On utilise le chemin pour récuperer les tokens et initialiser les clients slack
        self.__set_token_from_conf(str_path, str_token)

# =====================================================================================================================
# Setters / Getters
# =====================================================================================================================

    def __set_token_bot(self, str_token_bot):
        """Fonction de set du token de bot.

        Parameters
        ----------
        str_token_bot : str
            le token de bot.
        """
        # On set l'attribut str_token_bot pour pouvoir y acceder plus tard on sait jamais
        self.str_token_bot = str_token_bot
        # On lance le client slack du bot (sert à envoyer des messages)
        self.sc_bot = slack.WebClient(str_token_bot)

    def __set_token_user(self, str_token_user):
        """Fonction de set du token côté user.

        Parameters
        ----------
        str_token_bot : str
            le token côté user.
        """
        # On set l'attribut str_token_user pour pouvoir y acceder plus tard on sait jamais
        self.str_token_user = str_token_user
        # On lance le client slack côté user (sert à récuperer et effacer des messages)
        self.sc_user = slack.WebClient(str_token_user)

    def __set_token_from_conf(self, str_path, str_token):
        """Set des tokens à partir d'un chemin et d'un yaml.

        Parameters
        ----------
        str_path:  str
            le chemin du yaml contenant les tokens.
        str_token: str
            le nom du bot pour lequel récuperer les tokens.
        """
        # On set les tokens
        self.__set_token_bot(TOKEN_BOT)
        self.__set_token_user(TOKEN_USER)

    def __set_sp(self, sp):
        """Set le progress bar pour slack.

        Parameters
        ----------
        sp: obj
            L'objet SlackProgress.
        """
        self.sp = sp

    def __set_sbar(self, sbar):
        """Set la bar slack.

        Parameters
        ----------
        sbar: obj
            La barre de progression.
        """
        self.sbar = sbar

    def get_token_bot(self):
        """Fonction de récuperation du token du bot.

        Inutilisé pour le moment
        """
        return self.str_token_bot

    def get_token_user(self):
        """Fonction de récuperation du token côté bot.

        Inutilisé pour le moment
        """
        return self.str_token_user

# =====================================================================================================================
# Récuperation chaînes et messages
# =====================================================================================================================

    def get_list_channels(self):
        """Fonction de récuperation de la liste des chaînes.

        Utile car les chaînes ont des id que les autres fonctions utilisent

        Returns
        -------
        dict_channels: dict
            Le dictionnaire contenant les chaînes et leurs méta-data.
        """
        # Appel de la fonction channels.list sur le token user
        dict_channels_total = self.sc_user.channels_list()
        # Création d'un dictionnaire avec les noms communs des chaînes et leurs id
        dict_channels = dict(zip([channel['name'] for channel in dict_channels_total['channels']],
                                 [channel['id'] for channel in dict_channels_total['channels']]))

        return dict_channels

    def get_list_message(self, dict_channels, str_channel):
        """Fonction des récuperation des messages d'une chaîne.

        Parameters
        ----------
            dict_channels: dict
                le dictionnaire contenant les chaînes
            str_channel: str
                le nom de la chaîne à traiter

        Returns
        -------
        dict_channels: dict
            Le dictionnaire contenant les messages de la chaîne.
        """
        dict_messages = self.sc_user.channels_history(channel=dict_channels[str_channel])

        return dict_messages

    def get_user_from_name(self, str_name):
        """Fonction pour obtenir un user ID à partir de son nom.

        Parameters
        ----------
        str_name : str
            Le nom de la personne à chercher.

        Returns
        -------
        str_id: str
            L'ID de la personne.
        """
        dict_users = self.sc_user.users_list().data

        lst_names = [member['profile']['real_name'] for member in dict_users['members']]

        lst_best_names = process.extractBests(str_name, lst_names, score_cutoff=80)

        if len(lst_best_names) == 1:
            str_name_new = lst_best_names[0][0]
        else:
            for i in range(0, len(lst_best_names)):
                print(str(i + 1) + ' : ' + lst_best_names[i][0])
            index_name = term.force_read(term.read_numeric, "Choix : ", True, 1, len(lst_best_names) + 1)
            str_name_new = lst_best_names[index_name - 1][0]

        str_id = [member['id'] for member in dict_users['members'] if
                  member['profile']['real_name'] == str_name_new][0]

        return str_id

# =====================================================================================================================
# Envoi et suppression de messages
# =====================================================================================================================

    def init_sbar(self, total=100, str_channel=None, str_user=None):
        """Fonction d'initilisation de la progress bar.

        Parameters
        ----------
        total: int
            La limite de la barre de progression.
        str_channel: str
            le nom de la chaine sur laquelle afficher la progress bar.
        """
        if str_user is not None:
            str_id = self.get_user_from_name(str_user)
            self.__set_sp(SlackProgress(self.get_token_bot(), str_id))
            self.__set_sbar(self.sp.new(total=total))
        else:
            self.__set_sp(SlackProgress(self.get_token_bot(), str_channel))
            self.__set_sbar(self.sp.new(total=total))

    def sbar_set(self, pos):
        """Fonction d'évolution de la progress bar.

        Parameters
        ----------
        pos: int
            pos: la nouvelle position de la progress bar en pourcentage.
        """
        self.sbar.pos = pos

    def notify(self, str_message, str_channel=None, str_user=None):
        """Pour envoyer un message via le slack notifier.

        Parameters
        ----------
        str_message : str
            Le message en envoyer.
        str_channel : str, optional
            La chaîne ou poster le message. The default is 'projet'.

        Returns
        -------
        response : obj
            La réponse de slack.
        """
        # On vérifie que la connection à internet soit bien faite sinon ça plante
        bool_is_internet_on = slack_notifications.internet_on()
        response = False
        if bool_is_internet_on:
            # Si on est bien conncté alors on envoie le message
            if (str_user is not None) and (str_channel is not None):
                str_user = self.get_user_from_name(str_user)
                response = self.sc_bot.chat_postEphemeral(
                  channel=str_channel,
                  text=str_message,
                  user=str_user
                )
            elif str_user is not None:
                str_user = self.get_user_from_name(str_user)
                response = self.sc_bot.chat_postMessage(
                  channel=str_user,
                  text=str_message
                )
            elif str_channel is not None:
                response = self.sc_bot.chat_postMessage(
                    channel=str_channel,
                    text=str_message
                )
            else:
                response = None

        return response

    def delete_messages(self, str_channel, bool_bot_only=True):
        """Fonction de suppression des message d'une chaîne.

        Parameters
        ----------
        str_channel: str
            le nom de la chaîne à traiter.
        bool_bot_only: bool
            booléen indiquant si on efface que les messages écrits par un bot ou tous les messages.
        """
        # On verifie que la connection à internet soit bien faite
        bool_is_internet_on = slack_notifications.internet_on()
        if bool_is_internet_on:
            # On récupère la liste des chaines pour avoir l'ID de la chaîne à traiter
            dict_channels = self.get_list_channels()

            int_compteur_effacage = 1
            while int_compteur_effacage != 0:
                # On récupère l'ensemble des messages de la chaîne
                dict_messages = self.get_list_message(dict_channels, str_channel)

                str_id_channel = dict_channels[str_channel]

                # On compte si on efface des trucs ou pas, quand on efface plus rien, on a terminé, on sort du while
                int_compteur_effacage = 0
                for message in dict_messages['messages']:
                    # Pour chaque message on vérifie si il est écrit par un bot ou non et
                    # si on veut effacer les messages humains
                    if ('bot_id' in message) or ('client_msg_id' in message and not bool_bot_only):
                        # On récupère le time stamp, nécessaire pour effacer un message
                        ts = message['ts']
                        self.sc_user.chat_delete(channel=str_id_channel, ts=ts)
                        int_compteur_effacage += 1


# =====================================================================================================================
# Envoi de message sans passer par un objet
# =====================================================================================================================

    @classmethod
    def send_notification(cls, str_message, str_token, str_channel=None, str_user=None, bool_as_user=False):
        """Si on veut envoyer un message sans avoir à créer un slack notifier.

        Parameters
        ----------
        str_message: str
            Le message à envoyer.
        str_token: str
            Le token à utiliser.
        str_chnnel: str
            Le nom de la chaîne ou oster le message.
        bool_as_user: bool
            ?.

        Returns
        -------
        response: obj
            La réponse de slack.
        """
        # On vérifie qu'une connection à internet existe
        bool_is_internet_on = slack_notifications.internet_on()
        response = False
        if bool_is_internet_on:
            # On établit la connection à slack
            sc = slack.WebClient(str_token)
            # On envoie le message
            response = sc.chat_postMessage(channel=str_channel, text=str_message, as_user=bool_as_user)

        return response

    @staticmethod
    def internet_on():
        """Methode qui verifie si une connexion a internet existe ou non."""
        try:
            # Connexion à l'hôte
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            pass
        return False
