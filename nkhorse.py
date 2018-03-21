# -*- coding: utf-8 -*-
import os
import re
import numpy as np
import scipy as sp
import pandas as pd
import math
import requests
from bs4 import BeautifulSoup

class nkhorse(object):
    horseID = None
    name = None
    gender = None
    soup = None
    results = None
    pedigree = None
    summary = None
    root = 'http://db.netkeiba.com/horse/'

    re_nrac = re.compile('\d+(?=戦)')
    re_win = re.compile('\d+(?=勝)')
    re_fst = re.compile('(?<=\[)\d+(?=\s?-)')
    re_scd = re.compile('\d+(?=-\s?\d+\s?-\s?\d+\s?\])')
    re_trd = re.compile('\d+(?=-\s?\d+\s?\])')
    re_otr = re.compile('\d+(?=\s?\])')
    re_gndr = re.compile('(牡|牝|セ)')

    def __init__(self, horsenb):
        self.horseID = str(horsenb)
        self.setpage()
        self.setname()
        self.setresults()
        self.setpedigree()
        self.setsummary()

    def setpage(self):
        response = requests.get(self.root + self.horseID)
        response.encoding = response.apparent_encoding
        self.soup = BeautifulSoup(response.text, 'html.parser')

    def setname(self):
        horsetitle = self.soup.find('div', class_='horse_title')
        genderc = horsetitle.find('p', class_='txt_01').text
        self.name = horsetitle.h1.text.replace('\u3000', '')
        self.gender = nkhorse.re_gndr.findall(genderc)[0]

    def setsummary(self):
        proftable = self.soup.findAll('table', class_='db_prof_table no_OwnerUnit')[0]
        self.summary = dict()
        for a in proftable.findAll('tr'):
            self.summary[a.th.text] = a.td.text.replace('\n', '')
        wlsummary = self.summary['通算成績']
        prcs = ['re_nrac', ' re_win', ' re_fst', 're_scd', 're_trd', 're_otr']
        for i, attr in enumerate(['nrace', 'nwin', 'nfirst', 'nsecond', 'nthird', 'nother']):
            self.summary[attr] = eval('nkhorse.' + prcs[i] + '.findall(wlsummary)[0]')

    def setresults(self):
        self.results = pd.read_html(self.root + 'result/' + self.horseID)[0]

    def setpedigree(self):
        rawped = pd.read_html(self.root + 'ped/' + self.horseID)[0]
        self.pedigree = self.aligntoped(rawped)

    def setroot(self, root):
        self.root = root

    def aligntoped(self, df):
        dfdic = dict()
        nrow, ncol = df.shape
        for i in range(nrow):
            lis = []
            for j in range(ncol):
                val = df.iloc[i, j]
                if type(val) == float and math.isnan(val):
                    continue
                lis.append(df.iloc[i, j])
            dfdic[i] = lis

        df2 = df.copy()
        for i in range(nrow):
            offset = ncol - len(dfdic[i])
            for j in range(ncol):
                if j < offset:
                    df2.iloc[i, j] = np.nan
                else:
                    df2.iloc[i, j] = dfdic[i][j - offset]

        return df2