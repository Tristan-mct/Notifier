#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 21:58:12 2019.

@author: tristan
"""

# =====================================================================================================================
# Classe d'erreurs spécifiques aux saisies clavier
# =====================================================================================================================


class InputException(Exception):
    """Erreur de saisie."""

    def __init__(self, message):
        """Constructeur de l'erreur."""
        super(InputException, self).__init__(message)


# =====================================================================================================================
# Module de gestion des saisies
# =====================================================================================================================


class InputManager:
    """Manager de saisie clavier."""

    def read_line(str_prompt, bool_case=False, set_char=None):
        """Fonction de lecture d'une chaine de caractère.

        On prompt une saisie utilisateur et on regarde si elle appartient à un ensemble de mots attendus.

        Parameters
        ----------
        str_prompt: str
            le prompt affiché en premier pour demander la saisie.
        bool_case: bool
            booléen indiquant si la saisie doit respecter la casse ou non.
        set_char: set
            ensemble de valeurs que peuvent prendre la saisie.

        Returns
        -------
        str_input: str
            La chaine saisie et testée.
        """
        str_input = input(str_prompt)  # Récuperation de la saisie

        # Test un peu basique mais c'est surtout pour en rajouter plus tard si il faut
        if str_input is None:
            raise InputException("Erreur de saisie !")

        # Si on veut verifier que la saisie est dans un ensemble donné, on se demande tout d'abord
        # si il doit respecter la case
        str_test = str_input
        if not bool_case:
            str_test = str_input.lower()
            if set_char is not None:
                set_char = [x.lower() for x in set_char]

        # Si un ensemble est fourni alors on vérifie que l'input en fait partie
        if set_char is not None and str_test not in set_char:
            raise InputException("Erreur de saisie !")

        return str_input

    def read_char(str_prompt, bool_case=True, set_char=None):
        """Fonction de lecture d'un seul caractère eventuellement dans un ensemble.

        On demande à l'utilisateur de ne saisir qu'un seul caractère. Si on fournit un ensemble de test
        on compare la saisie à cet ensemble pour valider la saisie.

        Parameters
        ----------
        str_prompt: str
            le prompt affiché en premier pour demander la saisie.
        bool_case: bool
            booléen indiquant si la saisie doit respecter la casse ou non.
        set_char: set
            un ensemble de char à choisir.

        Returns
        -------
        str_input: str
            La saisie.
        """
        str_input = InputManager.read_line(str_prompt)  # récuperation sécurisée de la saisie

        # Si on veut verifier que la saisie est dans un ensemble donné, on se demande tout d'abord
        # si il doit respecter la case
        str_test = str_input
        if not bool_case:
            str_test = str_input.lower()
            if set_char is not None:
                set_char = [x.lower() for x in set_char]

        # Si un ensemble est fourni alors on vérifie que l'input en fait partie
        if (set_char is not None and str_test not in set_char) or len(str_test) > 1:
            raise InputException("Erreur de saisie !")

        return str_input

    def read_yes_no(str_prompt):
        """Fonction de lecture d'une réponse oui ou non à une question donnée.

        On compare la saisie à un ensemble de valeurs qui correspondent à oui où non. La casse n'est pas importante.

        Paramters
        ---------
        str_prompt: str
            le prompt affiché au début pour demander la saisie à l'utilisateur.

        Returns
        -------
        str_input: str
            La réponse.
        """
        # Fonction "préfabriquée" pour récuperer un oui ou un non
        str_input = InputManager.read_line(str_prompt, False, ['y', 'n', 'o', 'yes', 'no', 'oui', 'non'])

        return str_input

    def read_true_false(str_prompt):
        """Fontion de lecture d'un booléen.

        Fonction de lecture d'une réponse oui ou non à une question donnée
        Avec conversion en True ou False.

        Parameters
        ----------
        str_prompt: str
            le prompt affiché au début pour demander la saisie à l'utilisateur.

        Returns
        -------
        str_input: str
            La réponse.
        """
        # Fonction "préfabriquée" pour récuperer un oui ou un non
        str_input = InputManager.read_line(str_prompt, False, ['y', 'n', 'o', 'yes', 'no', 'oui', 'non', 'T', 'F',
                                                               'V', 'False', 'True', 'Vrai', 'Faux'])

        bool_input = False
        if str_input.lower() in [word.lower() for word in ['y', 'yes', 'o', 'oui', 'T', 'V', 'True', 'Vrai']]:
            bool_input = True

        return bool_input

    def read_numeric(str_prompt, bool_int=True, num_borne_inf=None, num_borne_sup=None,
                     bool_bi_incluse=True, bool_bs_incluse=True):
        """Fonction de lecture d'un numérique (entier ou non) borné ou non.

        Parameters
        ----------
        str_prompt: str
            l'invite de commande affiché au début pour demander la saisie à l'utilisateur.
        bool_int: bool, optional
            un booleen indiquant si on attend un entier ou non. The default is True.
        num_borne_inf: num, optional
            la borne inférieur, entière ou non. The default is None.
        num_borne_sup: num, optional
            la borne supérieur, entière ou non. The default is None.
        bool_bi_incluse: bool, optional
            Indique si la borne inférieur est incluse ou non. The default is True.
        bool_bs_incluse: num, optional
            Indique si la borne supérieur est incluse ou non. The default is True.

        Returns
        -------
        str_input: str
            La saisie.
        """
        str_input = InputManager.read_line(str_prompt)  # récuperation sécurisée de la saisie

        # On verifie tout d'abord que la saisie est numérique (est-ce qu'elle peut être convertie en float)
        try:
            float(str_input)
        except ValueError:
            raise InputException("La saisie doit être numérique")

        # Si c'est le cas on la convertie en int ou en float en fonction
        if bool_int:
            try:
                str_input = int(str_input)
            except ValueError:
                raise InputException("La saisie doit être un entier")
        else:
            try:
                str_input = float(str_input)
            except ValueError:
                raise InputException("Erreur inconnue")

        # Puis on s'occupe des bornes, on construit le test et on l'évalue
        if num_borne_sup is not None:
            test_sup = "<=" + str(num_borne_sup) if bool_bs_incluse else "<" + str(num_borne_sup)
            if not eval(str(str_input) + test_sup):
                raise InputException("La saisie est trop grande")

        if num_borne_inf is not None:
            test_sup = ">=" + str(num_borne_inf) if bool_bi_incluse else ">" + str(num_borne_inf)
            if not eval(str(str_input) + test_sup):
                raise InputException("La saisie est trop petite")

        return str_input

    def force_read(fun_reader, *argv):
        """Fonction qui boucle tant que la saisie est incorrecte.

        Fonction qui force la saisie en attrapant les erreurs de saisie
        et en en demandant une nouvelle

        Parameters
        ----------
        fun_reader: function
            la fonction de saisie.
        *argv: list
            les arguments de la fonction choisie.

        Returns
        -------
        str_input: str
            La saisie.
        """
        bool_intput_ok = False
        # Tant que la saisie est incorrecte
        while not bool_intput_ok:
            try:
                # Appel de la fonction de saisie
                str_input = fun_reader(*argv)
                bool_intput_ok = True
            except InputException as e:
                print(e)

        return str_input
