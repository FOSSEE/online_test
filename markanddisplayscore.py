from yaksh.models import Quiz
from yaksh.views import *
def markquestions(lst1, lst2):
    return list(set(lst1) & set(lst2))

def displayscore(ans,user_inputs):
    len_of_input=len(ans)
    score=len(markquestions(ans,user_inputs))
    print("your score is:  ",score, '/',len_of_input)
                           


def get_questionid():
    print(models.Quiz)