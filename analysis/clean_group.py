from yaksh.models import *
import numpy as np
    
group = []

for course in Course.objects.all():
    name = course.name.lower()
    if 'iscp' in name:
        new_group = 'Instructor'
    else:
        new_group = 'Self'

    group.append([name, new_group])

    course.group = new_group
    course.save()

group = np.array(group)
print(np.unique(group[:, 1:], return_counts=True))