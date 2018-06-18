from yaksh.models import *
import pandas as pd

def prefix_cols(df, prefix):
	df.columns = [prefix + '_' + str(col) if not str(col).startswith(prefix) else str(col) for col in df.columns]
	return df

#need (course tag)
course = pd.DataFrame(list(Course.objects.filter(is_trial=False).values('id', 'name', 'active', 'start_enroll_time', 'end_enroll_time')))
course['start_enroll_time'] = course.apply(lambda row: row['start_enroll_time'].strftime('%d-%m-%Y'), axis=1)
course['end_enroll_time'] = course.apply(lambda row: row['end_enroll_time'].strftime('%d-%m-%Y'), axis=1)
course = prefix_cols(course, 'course')
#course.rename(columns={'id' : 'course_id'}, inplace=True)

course_status = pd.DataFrame(list(CourseStatus.objects.values('user_id', 'course_id', 'grade')))

#user = pd.DataFrame(list(User.objects.values()))
#user = prefix_cols(user, 'user')

#need (gender) and (position cleaning)
profile = pd.DataFrame(list(Profile.objects.values('department', 'institute', 'position', 'user_id')))
profile = prefix_cols(profile, 'user')
#profile.rename(columns={'id' : 'user_id'}, inplace=True)

data = pd.merge(course_status, course, on='course_id')
data = pd.merge(data, profile, on='user_id')
#data = pd.merge(cross_join1, cross_join2, on='user_id')

data.to_csv('analysis/data.csv', index=False)
