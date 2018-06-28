from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from yaksh.models import *
import json
import pandas as pd
import numpy as np
import calendar
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from yaksh.decorators import email_verified, has_profile
from yaksh.views import is_moderator


############################moderator side report##################################

#main function that generates view
@login_required
@email_verified
def final_summary(request):

	user = request.user
	if not user.is_authenticated() or not is_moderator(user):
		raise Http404('You are not allowed to view this page!')

	return render(request, 'final_summary.html')

PASS_GRADES = ['A+', 'A', 'B+', 'B', 'C']

def nested_dict(n):
    if n == 2:
        return defaultdict(dict)
    else:
        return defaultdict(lambda: nested_dict(n-1))
    
#########################coursewise fns##############################
def make_group(data, catt):
    
    group = nested_dict(6)
    grouped = data.pivot_table(columns=['course_group', 'course_tag', 'year', 'month'], index = catt, values='course_id',aggfunc='count', fill_value=0).unstack().reset_index().rename(columns={0:'count'})
    for index, row in grouped.iterrows():
            group[row['course_group']][row['course_tag']][catt][row['year']][row['month']][row[catt]] = row['count']
            
    
    grouped_all = data.pivot_table(columns=['course_tag', 'year', 'month'], index = catt, values='course_id',aggfunc='count', fill_value=0).unstack().reset_index().rename(columns={0:'count'})
    #grouped_all = data.groupby(['course_tag', 'year', 'month', catt])[catt].agg(['count']).reset_index()
    for index, row in grouped_all.iterrows():
            group['All'][row['course_tag']][catt][row['year']][row['month']][row[catt]] = row['count']
    
    #pass count only for grades    
    if catt =='grade':
        
        for index, row in grouped.iterrows():
            if 'Passed' not in group[row['course_group']][row['course_tag']][catt][row['year']][row['month']]:
                group[row['course_group']][row['course_tag']][catt][row['year']][row['month']]['Passed'] = 0
            if row[catt] in PASS_GRADES:
                group[row['course_group']][row['course_tag']][catt][row['year']][row['month']]['Passed'] += row['count']
        
        for index, row in grouped_all.iterrows():
            if 'Passed' not in group['All'][row['course_tag']][catt][row['year']][row['month']]:
                group['All'][row['course_tag']][catt][row['year']][row['month']]['Passed'] = 0
            if row[catt] in PASS_GRADES:
                group['All'][row['course_tag']][catt][row['year']][row['month']]['Passed'] += row['count']
        
    
    #enrolled count
    counts = data.groupby(['course_group', 'course_tag', 'year', 'month'])['month'].agg(['count']).reset_index()
    for index, row in counts.iterrows():
        group[row['course_group']][row['course_tag']][catt][row['year']][row['month']]['Enrolled'] = row['count']
    
    counts_all = data.groupby(['course_tag', 'year', 'month'])['month'].agg(['count']).reset_index()
    for index, row in counts_all.iterrows():
        group['All'][row['course_tag']][catt][row['year']][row['month']]['Enrolled'] = row['count']
    
    return group

#enroll count per level
def get_enroll_count_perlevel(data, final):
    counts = data.groupby(['course_group', 'course_tag'])['course_tag'].agg(['count']).reset_index()
    for index, row in counts.iterrows():
        final[row['course_group']][row['course_tag']]['Enrolled'] = row['count']
        
    counts_all = data.groupby(['course_tag'])['course_tag'].agg(['count']).reset_index()
    for index, row in counts_all.iterrows():
        final['All'][row['course_tag']]['Enrolled'] = row['count']
        
    return final

#pass count per level
def get_grade_count_perlevel(data, final, grades):
    
    global PASS_GRADES
    
    counts = data.groupby(['course_group', 'course_tag', 'grade'])['grade'].agg(['count']).reset_index()
    for index, row in counts.iterrows():
        if row['grade'] in grades:
            final[row['course_group']][row['course_tag']][row['grade']] = row['count']
        if row['grade'] in PASS_GRADES:
            if 'Passed' not in final[row['course_group']][row['course_tag']]:
                final[row['course_group']][row['course_tag']]['Passed'] = 0
            final[row['course_group']][row['course_tag']]['Passed'] += row['count'] 
            
    counts_all = data.groupby(['course_tag', 'grade'])['grade'].agg(['count']).reset_index()
    for index, row in counts_all.iterrows():
        if row['grade'] in grades:
            final['All'][row['course_tag']][row['grade']] = row['count']
        if row['grade'] in PASS_GRADES:
            if 'Passed' not in final['All'][row['course_tag']]:
                final['All'][row['course_tag']]['Passed'] = 0
            final['All'][row['course_tag']]['Passed'] += row['count'] 
    
    return final
    
def merge(data, catts):
    
    groups = []
      
    for catt in catts:
        group = make_group(data, catt)
        groups.append(group)
    
    final = nested_dict(3)
    
    group_keys = list(data['course_group'].unique()) + ['All']    
    level_keys = data['course_tag'].unique()
    
    for i, group in enumerate(groups):
        for group_key in group_keys:
            for level_key in level_keys:
                final[group_key][level_key][catts[i]] = group[group_key][level_key][catts[i]]

    final = get_enroll_count_perlevel(data, final)
    final = get_grade_count_perlevel(data, final, ['A+', 'A'])

    return final

###########################main fn to get all data############################

def get_data(start_date, end_date):
	data = pd.read_csv('analysis/cleaned_data.csv')
	data['course_start_enroll_time'] = pd.to_datetime(data['course_start_enroll_time'], format='%d-%m-%Y')
	mask = (data['course_start_enroll_time'] >= start_date) & (data['course_start_enroll_time'] <= end_date)
	data = data.loc[mask]

	if data.empty:
		return {}

	months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
	data['month'] = data['course_start_enroll_time'].apply(lambda row: months[row.month-1])
	data['year'] = data['course_start_enroll_time'].apply(lambda row: str(row.year))

	
	######################## coursewise ######################################	
	coursewise = merge(data, ['grade', 'user_gender', 'user_position', 'user_age_group'])

	######################## statewise ######################################
	statewise = nested_dict(2)

	enrolled = data.groupby(['course_group', 'state'])['state'].agg(['count']).reset_index()
	for index, row in enrolled.iterrows():
	    statewise[row['course_group']][row['state']] = row['count']
	  
	enrolled_all =  data.groupby(['state'])['state'].agg(['count']).reset_index()
	for index, row in enrolled_all.iterrows():
	    statewise['All'][row['state']] = row['count']

	######################### institutewise ################################	    
	institutewise = nested_dict(4)

	#enrolled per institute in groups
	enrolled = data.groupby(['course_group', 'institute'])['institute'].agg(['count']).reset_index()
	for index, row in enrolled.iterrows():
	    institutewise[row['course_group']][row['institute']]['Enrolled'] = row['count']

	#passed per institute in groups    
	passed = data[data['grade'] != 'F'].groupby(['course_group', 'institute'])['institute'].agg(['count']).reset_index()
	for index, row in passed.iterrows():
	    institutewise[row['course_group']][row['institute']]['Passed'] = row['count']

	#enrolled per institute per courese in groups
	enrolled_percourse = data.groupby(['course_group', 'institute', 'course_name'])['course_name'].agg(['count']).reset_index()
	for index, row in enrolled_percourse.iterrows():
	    institutewise[row['course_group']][row['institute']][row['course_name']]['Enrolled'] = row['count']

	#passed per institute per courese in groups
	passed_percourse = data[data['grade'] != 'F'].groupby(['course_group', 'institute', 'course_name'])['course_name'].agg(['count']).reset_index()
	for index, row in passed_percourse.iterrows():
	    institutewise[row['course_group']][row['institute']][row['course_name']]['Passed'] = row['count']
	    
	#enrolled per institute all
	enrolled_all = data.groupby(['institute'])['institute'].agg(['count']).reset_index()
	for index, row in enrolled_all.iterrows():
	    institutewise['All'][row['institute']]['Enrolled'] = row['count']

	#passed per institute all    
	passed_all = data[data['grade'] != 'F'].groupby(['institute'])['institute'].agg(['count']).reset_index()
	for index, row in passed_all.iterrows():
	    institutewise['All'][row['institute']]['Passed'] = row['count']

	#enrolled per institute per courese all
	enrolled_all_percourse = data.groupby(['institute', 'course_name'])['course_name'].agg(['count']).reset_index()
	for index, row in enrolled_all_percourse.iterrows():
	    institutewise['All'][row['institute']][row['course_name']]['Enrolled'] = row['count']

	#passed per institute per courese all
	passed_all_percourse = data[data['grade'] != 'F'].groupby(['institute', 'course_name'])['course_name'].agg(['count']).reset_index()
	for index, row in passed_all_percourse.iterrows():
	    institutewise['All'][row['institute']][row['course_name']]['Passed'] = row['count']

	final = {}
	final['coursewise'] = dict(coursewise)
	final['statewise'] = dict(statewise)
	final['institutewise'] = dict(institutewise)

	return final

#function that returns the required data in json format
@csrf_exempt
@login_required
@email_verified
def final_summary_data(request):

	user = request.user
	if not user.is_authenticated() or not is_moderator(user):
		return HttpResponse('You are not allowed to access this data!')

	received = json.loads(request.body)

	start_date = received['start_date']
	end_date = received['end_date']

	start_date = datetime.strptime(str(start_date), '%Y%m')
	end_date = datetime.strptime(str(end_date), '%Y%m')
	end_date = end_date.replace(day = calendar.monthrange(end_date.year, end_date.month)[1])

	#print(start_date)
	#print(end_date)

	final = get_data(start_date, end_date)

	#return HttpResponse();
	return HttpResponse(json.dumps(final), content_type='application/json')
#################################################################################

##################################student side report############################

@login_required
@email_verified
def view_quiz_stats(request, course_id, question_paper_id):
	user = request.user
	questionpaper = QuestionPaper.objects.get(id=question_paper_id)
	quiz_stats, que_stats = questionpaper.get_quiz_stats(user, course_id)
	#print(que_stats)
	return render(request, 'view_quiz_stats.html', {'quiz_stats' : quiz_stats, 'que_stats' : que_stats})

#################################################################################