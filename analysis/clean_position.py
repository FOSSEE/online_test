#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 02:07:57 2018

@author: skt
"""

from yaksh.models import *
import numpy as np
from yaksh.views import is_moderator

default = ["Faculty", "School Student", "Graduate Student", 
                "Postgraduate Student", "Industry Professional", 
                "Research Scholar"]

position = []

profiles = Profile.objects.all()
for profile in profiles:
    val = profile.position.lower()

    # if 'teacher' in val or 'prof' in val or 'faculty' in val or \
    # 'instuct' in val or 'assist' in val or 'lect' in val:
        #print(profile.user, val, is_moderator(profile.user))
        
    if is_moderator(profile.user):
        new_val = 'Faculty'

    elif val == '' or 'b.tech' in val or val=='student' or 'year' in val or 'fresh' in val \
        or 'sem' in val or val.isdigit() or 'btech' in val:
        new_val = 'Graduate Student'    

    elif 'm.tech' in val or 'post' in val or 'mtech' in val or 'master' in val:
        new_val = 'Postgraduate Student' 

    elif 'engineer' in val or 'professional' in val or 'industry' in val or 'manage' in val \
            or 'dev' in val or 'program' in val or 'soft' in val:
        new_val = 'Industry Professional'        

    elif 'research' in val:
        new_val = 'Research Scholar'
    
    elif 'school' in val:
        new_val = 'School Student'
    else:
        new_val = 'Graduate Student'
    
    position.append([val, new_val])
    #print(val, new_val)

    profile.position = new_val
    profile.save()

position = np.array(position)
print(np.unique(position[:, 1:], return_counts=True))