#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 13:58:25 2018.

@author: tristan
"""


# =====================================================================================================================
# Import et librairies
# =====================================================================================================================


import time                                # Pour attendre entre les demandes d'IP
import datetime                            # Pour les time stamps des messages d'erreur
import os                                  # Pour verifier si un service est actif
import re                                  # Retraitement des strings
import socket                              # Pour verifier si internet est on
import subprocess                          # Pour verifier si un service est actif
import requests                            # Version 2.10, utilisé pour récuperer les pages web
import urllib.request as urllib            # Pour se connecter au proxy
import random as rdm                       # Pour randomiser les user agents
from bs4 import BeautifulSoup              # Reformate les pages scrapées
from stem import Signal                    # Pour se connecter à TOR
from stem.control import Controller        # Pour se connecter à TOR
from operator import itemgetter            # Iterateurs sur un pandas


# =====================================================================================================================
# Module de gestion de connexion
# =====================================================================================================================

class ConnectionManager:
    """Fonction de management des connexion."""

# =====================================================================================================================
# Initialisation, accesseurs
# =====================================================================================================================

    def __init__(self, str_pswd, str_path_user_agent_lists):
        """Fonction d'initialisation du manager de connexion.

        Les IP sont misent à 0 seront attribuées plus tard.
        Les user agents sont issu d'un fichier à part, ou alors on utilise l'UA par défault.

        Parameters
        ----------
        str_pswd : str
            Le mot de passe TOR.
        str_path_user_agent_lists : str
            Le chemin du fichier contenant la liste des user agents.
        """
        # Initialisation du connexion manager, les IP sont à 0.0.0.0 et sont changés plus tard
        self.new_ip = "0.0.0.0"
        self.old_ip = "0.0.0.0"
        self.user_agent = ""
        self.new_identity(str_pswd, str_path_user_agent_lists)

# =====================================================================================================================
# Connexions
# =====================================================================================================================

    def _get_connection(self, str_pswd):
        """Fonction qui lance une nouvelle connexion.

        Nouvelle connexion TOR ou pas.

        Parameters
        ----------
        str_pswd : str
            Le mot de passe TOR.
        """
        # On utilise le mot de passe TOR pour s'authentifier
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=str_pswd)
            controller.signal(Signal.NEWNYM)
            controller.close()

    def _set_url_proxy(self):
        """Request URL par le proxy local."""
        proxy_support = urllib.ProxyHandler({"http": "127.0.0.1:8118"})
        opener = urllib.build_opener(proxy_support)
        urllib.install_opener(opener)

    def request(self, url, str_path_user_agent_lists=None):
        """Fonction de requetage.

        Communication de la connexion (TOR ou non) par le proxy local.

        Parameters
        ----------
        url : str
            L'URL à requêter.
        str_path_user_agent_lists : str, optional
            La liste des user agents pour pimenter un peu le tout. The default is None.

        Returns
        -------
        request: obj
            Le résultat de la requête.
        """
        try:
            # Choix d'un user agent
            self._set_url_proxy()

            if str_path_user_agent_lists is not None:
                lst_user_agents = self.load_user_agent(str_path_user_agent_lists)
                self.user_agent = {'User-Agent': lst_user_agents[rdm.randint(0, len(lst_user_agents) - 1)]}
            else:
                self.user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,\
                                   like Gecko) Chrome/60.0.3112.113 Safari/537.36'}

            # Requetage
            request = urllib.Request(url, None, self.user_agent)

            request = urllib.urlopen(request)

            return request
        except urllib.HTTPError as e:
            return e

    def new_identity(self, str_pswd, str_path_user_agent_lists):
        """Fonction de demande d'une nouvelle identité.

        Fonction pour modifier l'IP, une fois de temps en temps'

        Parameters
        ----------
        str_pswd : str
            Le mot de passe TOR.
        str_path_user_agent_lists : str
            Le chemin du fichier contenant la liste des user agents.
        """
        self.old_ip = self.new_ip
        self._get_connection(str_pswd)
        self.new_ip = self.request("http://icanhazip.com/", str_path_user_agent_lists).read()

        seg = 0
        # Si on obtient la même IP on attend et on en redemande une autre
        while self.old_ip == self.new_ip:
            time.sleep(5)
            seg += 5
            self.new_ip = self.request("http://icanhazip.com/", str_path_user_agent_lists).read()

# =====================================================================================================================
# Outils
# =====================================================================================================================

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

    @staticmethod
    def is_service_running(name):
        """Fonction de vérification du status du service.

        Vérifie l'état du service à l'aide de la commande subprocess en cachant les outputs d'erreur et de sortie

        Parameters
        ----------
        name : str
            Nom du service à verifier.

        Returns
        -------
        bool
            Indique si le service est up.
        """
        with open(os.devnull, 'wb') as hide_output:
            int_status = subprocess.Popen(['/usr/sbin/service', name, 'status'], stdout=hide_output,
                                          stderr=hide_output).wait()

        return int_status == 0

    @staticmethod
    def load_user_agent(str_path_user_agent_lists):
        """Retourne une liste d'User-Agents.

        Lit le fichier contenant les User-Agents et les place dans une liste pour les
        retourner par la suite.

        Parameters
        ----------
        str_path_user_agent_lists : str
            Le chemin du fichier contenant les ser agents.

        Returns
        -------
        lst_user_agent : list
            La liste des user agents.
        """
        lst_user_agent = []
        with open(str_path_user_agent_lists, 'r') as file_useragent:
            for line in file_useragent:
                lst_user_agent.append(line.replace('\n', ''))

        file_useragent.close()

        return lst_user_agent

# =====================================================================================================================
# Outils de scraping
# =====================================================================================================================


class ScrapingTools:
    """Outils de scraping."""

    def soup_converter(str_url, str_path_user_agent_lists=None, dict_paths_conf=None, cm_tor=None, dict_tor=None):
        """Fonction de récuperation de l'arborescence HTML d'une page.

        A partir d'un url, on essaie de récuperer le contenu d'une page en utilisant TOR ou non.

        Parameters
        ----------
        str_url : str
            L'URL à scraper.
        str_path_user_agent_lists : str, optional
            Le chemin du fichier contenant les user agents. The default is None.
        dict_paths_conf : dict, optional
            Pour les parametres des user agents. The default is None.
        cm_tor : obj, optional
            Le Connexion Manager. The default is None.
        dict_tor : dict, optional
            parametres relatifs à TOR. The default is None.

        Raises
        ------
        requests
            Si une page ne répond pas et qu'on dépasse un nombre de tentatives de connexions.

        Returns
        -------
        soup : obj
            l'arborescence HTML de la page.
        """
        # Récupération de la page par requests
        bool_status = ConnectionManager.is_service_running('tor')
        # On compte les plantages, si ça plante trop de fois on arrete
        int_tries = 1
        # On regarde si le scraping a bien été fait
        bool_request_ok = False
        while int_tries < 5 and not bool_request_ok:
            try:
                # Requete par TOR
                if bool_status and cm_tor is not None:
                    req_page = cm_tor.request(str_url, str_path_user_agent_lists)
                    soup = BeautifulSoup(req_page.read(), "lxml")
                else:
                    # Requete sans TOR
                    req_page = requests.get(str_url)
                    # Récuperation du contenu au format text
                    html_content = req_page.text
                    # Conversion de la page HTML en soupe
                    soup = BeautifulSoup(html_content, 'lxml')
                bool_request_ok = True
            # Si il y a plantage de connexion
            except requests.exceptions.ConnectionError:
                # On affiche un message, on incrémente les compteurs
                print(str(datetime.datetime.now()) + " : Erreur de récuperation de la page")
                cm_tor.new_identity(dict_tor['tor_mdp'], dict_paths_conf['parametres_useragents'])
                int_tries += 1
                if int_tries == 5:
                    raise requests.exceptions.ConnectionError('Trop de tentatives de connexion à la page')

        # Si il y a erreur mais que ça fini par marcher on affiche ce message, ça permet de ne pas confondre
        # les plantages successifs sur des pages différentes
        if int_tries > 1:
            print(str(datetime.datetime.now()) + " : Scraping succès après plusieurs essais")

        return soup

    def soup_security(str_url, str_path_user_agent_lists=None, dict_paths_conf=None, cm_tor=None, dict_tor=None):
        """Fonction de récuperation de l'arborescence HTML en faisant attention à certaines sécurités.

        Parameters
        ----------
        str_url : str
            L'URL à scraper.
        str_path_user_agent_lists : str, optional
            Le chemin du fichier contenant les user agents. The default is None.
        dict_paths_conf : dict, optional
            Pour les parametres des user agents. The default is None.
        cm_tor : obj, optional
            Le Connexion Manager. The default is None.
        dict_tor : dict, optional
            parametres relatifs à TOR. The default is None.

        Raises
        ------
        requests
            Si une page ne répond pas et qu'on dépasse un nombre de tentatives de connexions.

        Returns
        -------
        soup : obj
            l'arborescence HTML de la page.
        """
        int_cpt = 1
        # On scrap la page
        soup = ScrapingTools.soup_converter(str_url, str_path_user_agent_lists,
                                            dict_paths_conf=dict_paths_conf, cm_tor=cm_tor, dict_tor=dict_tor)
        # Et si on tombe sur la version sécurisée de la page on retente mais ça n'arrive plus ça,
        # cette partie sert plus a rien normalement
        while soup.find('meta', {'name': 'captcha-bypass'}) is not None:
            print(str(datetime.datetime.now()) +
                  " : Erreur, on est arrivé sur la version sécurisé^du site (ne devrait pas arriver)")
            cm_tor.new_identity(dict_tor['tor_mdp'])
            soup = ScrapingTools.soup_converter(str_url, str_path_user_agent_lists,
                                                dict_paths_conf=dict_paths_conf, cm_tor=cm_tor, dict_tor=dict_tor)
            int_cpt += 1
            if int_cpt == dict_tor['nb_tries']:
                raise ValueError('Impossible de récuperer la page avec tor')

        while re.search('user-scalable=[a-z]{2,3}', soup.find('meta', {'name': 'viewport'}).
                        attrs['content']).group(0).split('=')[1] == 'no':
            print(str(datetime.datetime.now()) + " : Erreur, on est sur la version mobile du site")
            cm_tor.new_identity(dict_tor['tor_mdp'])
            soup = ScrapingTools.soup_converter(str_url, str_path_user_agent_lists,
                                                dict_paths_conf=dict_paths_conf, cm_tor=cm_tor, dict_tor=dict_tor)
            int_cpt += 1
            if int_cpt == dict_tor['nb_tries']:
                raise ValueError('Impossible de récuperer la page avec tor')

        return soup

    def clean_soup(html_bloc, index_bloc, index_elem, bool_full_line):
        """Nettoyage d'une ligne html.

        On recupere un bloc html, on enlève les caractères spéciaux, on split sur
        les espaces qui en resultent et on recupère les éléments voulus

        Parameters
        ----------
        html_bloc : str
            L'aborescende HTML brute.
        index_bloc : int
            L'index de l'élément à recuperer et retraiter dans le bloc.
        index_elem : int
            La liste des index des éléments qui recupere à la fin.
        bool_full_line : Indique si il s'agit d'une ligne entière
            bool.

        Returns
        -------
        str_clean_line : str
            La ligne nettoyée.
        """
        if bool_full_line:
            # S'il s'agit d'une ligne entière
            str_clean_line = re.sub(r'\s*[\t\n\r]+\s*', ' | ', html_bloc[index_bloc].text)[3:][:-3]
        elif len(index_elem) == 1:
            # Si il s'agit d'un seul élément
            str_clean_line = itemgetter(*index_elem)(re.sub(r'\s*[\t\n\r]+\s*', ' | ', html_bloc[index_bloc].
                                                            text)[3:][:-3].split(' | '))
        else:
            # Si il y a plusieurs éléments on converti en liste pour la cohérence de structure
            str_clean_line = list(itemgetter(*index_elem)(re.sub(r'\s*[\t\n\r]+\s*', ' | ', html_bloc[index_bloc].
                                                                 text)[3:][:-3].split(' | ')))
        return str_clean_line
