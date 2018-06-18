#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  5 23:57:33 2018

@author: skt
"""

import pandas as pd
import numpy as np

def grouping(name):
    name = name.lower()
    if 'iscp' in name:
        return 'Instructor'
    else:
        return 'Self'
    
###########################cleaning######################
data = pd.read_csv('data.csv')
data['grade'] = np.random.choice(list(['A+', 'A', 'B+', 'B', 'C', 'P', 'F']), len(data), p=[0.2, 0.2, 0.2, 0.15, 0.15, 0.07, 0.03])
data['course_group'] = data['course_name'].apply(lambda row: grouping(row))
data['course_tag'] =  np.random.choice(list(['Basic', 'Intermediate', 'Advanced']), len(data))
data['user_gender'] = np.random.choice(list(['Male', 'Female', 'Transgender']), len(data), p=[0.6, 0.3975, 0.0025])
data['user_position'] = np.random.choice(list(['School Student', 'Graduate Student', 'Postgraduate Student', 'Research Scolar', 'Faculty', 'Industry Professional', 'others']), len(data), p=[0.1, 0.5, 0.1, 0.025, 0.15, 0.1, 0.025])
data['user_age'] = np.random.choice(list(range(16,65)), len(data))
#data['user_age_group'] = pd.cut(data['user_age'], np.arange(0, 101, 10))
labels = ['1-15', '16-25', '26-35', '36-45', '46-55', '56-65', '66-75', '76-85']
data['user_age_group'] = pd.cut(data['user_age'], [0, 15, 25, 35, 45, 55, 65, 75, 85], labels=labels)
#data['user_age_group'] = data['user_age_group'].apply(lambda row : str(row).replace('(', '').replace(', ','_').replace(']',''))

from itertools import product
from string import ascii_uppercase
institutes = [''.join(i) for i in product(ascii_uppercase, repeat = 2)][:100]
states = open('states').read().split('\n\n')[:-1]
institute_details = [(institute, np.random.choice(states)) for institute in institutes]
choices = np.random.choice(len(institute_details), len(data))
institute_details = np.array(institute_details)
institute_details = institute_details[choices]
data['institute'], data['state'] = zip(*institute_details) 

data.to_csv('cleaned_data.csv', index=False)
