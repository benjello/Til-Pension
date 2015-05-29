# -*- coding: utf-8 -*-

from numpy import array, ndarray, in1d
from pandas import DataFrame
from til_pension.time_array import TimeArray
from til_pension.datetil import DateTil

compare_destinie = True


class PensionData(object):
    '''
    Class à envoyer à Simulation de Til-pension
    '''
    def __init__(self, workstate, salaire_imposable, info_ind):
        assert isinstance(workstate, TimeArray)
        assert isinstance(salaire_imposable, TimeArray)
        self.workstate = workstate
        self.salaire_imposable = salaire_imposable
        self.info_ind = info_ind
        if isinstance(info_ind, DataFrame):
            self.info_ind = info_ind.to_records(index=True)

        assert workstate.dates == salaire_imposable.dates
        dates = salaire_imposable.dates
        assert sorted(dates) == dates
        self.last_date = None  # intialisation for assertion in set_dates
        self.set_dates(dates)

    def set_dates(self, dates):
        self.dates = dates
        # on ne change pas last_date pour ne pas avoir d'incohérence avec date_liquidation
        if self.last_date is not None and DateTil(dates[-1]).liam != self.last_date.liam:
            raise Exception("Impossible to change last_date of a data_frame")
        self.last_date = DateTil(dates[-1])
        self.first_date = DateTil(dates[0])

    def selected_dates(self, first=None, last=None, date_type='year', inplace=False):
        ''' cf TimeArray '''
        if inplace:
            self.workstate.selected_dates(first, last, date_type, inplace=True)
            self.salaire_imposable.selected_dates(first, last, date_type, inplace=True)
            self.set_dates(self.salaire_imposable.dates)
        else:
            wk = self.workstate.selected_dates(first, last, date_type)
            sal = self.salaire_imposable.selected_dates(first, last, date_type)
            return PensionData(wk, sal, self.info_ind)

    def selected_regime(self, code_regime):
        ''' Cette fonction renvoie une copie corrigée de l'objet PensionData dans lequel :
        - tous les workstate de data.workstate qui ne figurent pas dans code_regime sont remplacés par 0
        - tous les salaires non-associés à un workstate dans code_regime sont remplacés par 0
        '''
        wk_selection = self.workstate.isin([code_regime])
        sal = self.salaire_imposable.copy()
        work = self.workstate.copy()
        wk_regime = TimeArray(wk_selection*work, sal.dates, name='workstate_regime')
        sal_regime = TimeArray(wk_selection*sal, sal.dates, name='salaire_imposable_regime')
        return PensionData(wk_regime, sal_regime, self.info_ind)

    def translate_frequency(self, output_frequency='month', method=None, inplace=False):
        ''' cf TimeArray '''
        if inplace:
            self.workstate.translate_frequency(output_frequency, method, inplace=True)
            self.salaire_imposable.translate_frequency(output_frequency, method, inplace=True)
            self.set_dates(self.salaire_imposable.dates)
        else:
            wk = self.workstate.translate_frequency(output_frequency, method)
            sal = self.salaire_imposable.translate_frequency(output_frequency, method)
            return PensionData(wk, sal, self.info_ind)

    @classmethod
    def from_arrays(cls, workstate, salaire_imposable, info_ind, dates=None):
        if isinstance(salaire_imposable, DataFrame):
            assert isinstance(workstate, DataFrame)
            try:
                assert all(salaire_imposable.index == workstate.index) and all(salaire_imposable.index == info_ind.index)
            except:
                assert all(salaire_imposable.index == workstate.index)
                assert len(salaire_imposable) == len(info_ind)
                sal = salaire_imposable.index
                idx = info_ind.index
                assert all(sal[sal.isin(idx)] == idx[idx.isin(sal)])
                # si on coince à ce assert ici c'est que l'ordre change
                print(sal[~sal.isin(idx)])
                print(idx[~idx.isin(sal)])
                # un décalage ?
                decal = idx[~idx.isin(sal)][0] - sal[~sal.isin(idx)][0]
                import pdb
                pdb.set_trace()

            # TODO: should be done before
            assert salaire_imposable.columns.tolist() == workstate.columns.tolist()
            assert salaire_imposable.columns.tolist() == (sorted(salaire_imposable.columns))
            dates = salaire_imposable.columns.tolist()
            salaire_imposable = array(salaire_imposable)
            workstate = array(workstate)

        if isinstance(salaire_imposable, ndarray):
            assert isinstance(workstate, ndarray)
            salaire_imposable = TimeArray(salaire_imposable, dates, name='salaire_imposable')
            workstate = TimeArray(workstate, dates, name='workstate')

        assert in1d(info_ind['sexe'], [0, 1]).all()
        return PensionData(workstate, salaire_imposable, info_ind)
