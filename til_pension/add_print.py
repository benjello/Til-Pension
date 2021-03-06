# -*- coding: utf-8 -*-

''' crée une fonction qui sert en fait de décorteur :
        - elle prend comme argument une fonction
        - elle retourne une fonctino
        - la différence entre l'entrée et la sortie c'est que
    la fonction de sortie affiche ses arguments (pour une liste
    d'indice donnée)
'''

import sys
from pandas import DataFrame, Series
from numpy import ndarray

from til_pension.time_array import TimeArray

def _to_print(key, val, selection_id, selection_ix, cache, intermediate=False):
    add_print = 'qui'
    if key in cache:
        return cache
    else:
        if intermediate:
            add_print = "est également appelé(e)/calculé(e) au cours du calcul et"
        if isinstance(val, dict):
            for child_key, child_val in val.iteritems():
                _to_print(child_key, child_val, selection_id, selection_ix, cache)
        elif isinstance(val, DataFrame):
            if selection_ix is None:
                selection_ix = range(len(val))
            print("    - La table pandas {} {} vaut: \n{}".format(key, add_print, val.iloc[selection_ix,:].to_string()))
            cache.append(key)
        elif isinstance(val, TimeArray):
            val_to_print =  DataFrame(val.array[selection_ix,:], columns=val.dates, index=selection_id)
            print("    - Le TimeArray {} {} vaut: \n{}".format(key, add_print, val_to_print.to_string()))
            cache.append(key)
        elif isinstance(val, ndarray):
            #It has to be a vetor, numpy matrix should be timearrays
            try:
                val_to_print = DataFrame(val[selection_ix], index=selection_id).to_string()
                print("    - Le vecteur {} {} vaut: \n {}".format(key, add_print, val_to_print)) #only for parameter ?
            except:
                pass
        elif isinstance(val, Series):
            if selection_ix is None:
                selection_ix = range(len(val))
            val_to_print = DataFrame(val.iloc[selection_ix], index=selection_id).to_string()
            print("    - Le vecteur {} {} vaut: \n {}".format(key, add_print, val_to_print))
        else:
            if key != 'self':
                print("    - L'objet {}".format(key))
            #cache.append(key) : probleme
        return cache


class AddPrint(object):
    def __init__(self, selected_ident, selected_index):
        '''
        - print_level : TODO
        doit mémoriser
        on a besoin du len_data pour les valeurs par défaut
        - selection est la liste de lignes à afficher
        '''
        self._locals = {}
        self.selected_index = selected_index #index format numpy
        self.selected_indent = selected_ident #identifiants sélectionnés
        self.cache = []

    def __call__(self, func):
        fname = func.__name__

        def call_func(*args):
            def tracer(frame, event, arg):
                if event=='return':
                    self._locals = frame.f_locals.copy()

            sys.setprofile(tracer)
            try:
                # trace the function call
                res = func(*args)
            finally:
                # disable tracer and replace with old one
                sys.setprofile(None)
            for key, val in self._locals.iteritems():
                self.cache = _to_print(key, val, self.selected_indent, self.selected_index, self.cache, intermediate=True)
            return res

        def wrapper(*args, **kwargs):
            print("Pour la fonction {}, les arguments appelés sont : ".format(fname))
            arg_name = ''
            args_names = []
            for arg in args:
                if hasattr(arg, 'name'):
                    arg_name = arg.name
                    args_names.append(arg_name)
                if hasattr(arg, '__name__'):
                    arg_name = arg.__name__
                    args_names.append(arg_name)
                self.cache = _to_print(arg_name, arg,self.selected_indent, self.selected_index, self.cache)
            return call_func(*args,**kwargs)
        return wrapper