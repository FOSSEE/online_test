from django.shortcuts import render
from django.utils import timezone
from .models import easy_standardtestcase
from .forms import easy_standardtestcaseForm
from django.shortcuts import redirect



def post_list(request):
    posts = easy_standardtestcase.objects.all()
    return render(request, 'easy_standardtestcase/post_list.html', {'posts': posts})


def post_detail(request,pk):
	post=easy_standardtestcase.objects.get(pk=pk)
	return render(request, 'easy_standardtestcase/post_detail.html', {'post': post})


def post_new(request):
    if request.method == "POST":
        form = easy_standardtestcaseForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            print ("=========",post)
            fn=form.data['function']
            typevar=form.data['typeval']
            inp=form.data['inputVals']
            op=form.data['operator']
            out=form.data['output']

            if form.data["lang"]=="python":
                post.final_standardtestcase='assert ' + fn + '(' + inp + ')' + op + out

            elif form.data["lang"]=="c" or form.data["lang"]=="cpp"  :
                post.final_standardtestcase='#include <stdlib.h>\nextern int ' + fn +'('+ typevar+')'+';\ntemplate <class T>\nvoid check(T expect,T result)\n{\nif (expect == result)\n{\nprintf("\\nCorrect:\\n Expected %d got %d \\n",expect,result);\n}\nelse\n{\nprintf("\\nIncorrect:\\n Expected %d got %d \\n",expect,result);\nexit (1);\n}\n}\nint main(void)\n{\nint result;\nresult = ' + fn + '('+inp+');\nprintf("Input submitted to the function:'+ inp+'");\ncheck('+out+',result);\nprintf("All Correct\\n");\n}'
            
            elif form.data["lang"]=="java":
                post.final_standardtestcase='class main\n{\npublic static <E> void check(E expect, E result)\n{\nif(result.equals(expect))\n{\nSystem.out.println("Correct:\nOutput expected "+expect+" and got "+result);\n}\nelse\n{\nSystem.out.println("Incorrect:\nOutput expected "+expect+" but got "+result);\nSystem.exit(1);\n}\n}\npublic static void main(String arg[])\n{\nTest t = new Test();\nint result, input, output;\ninput = '+inp+'; output = '+op+';\nresult = t.'+fn+'('+inp+');\nSystem.out.println("Input submitted to the function: "+input);\ncheck(output, result);\n}\n}'

            post.save()
            print ("cccccccccccccccccccccccccccccccccccccc")
            print(post.final_standardtestcase)
            return redirect('post_detail', pk=post.pk)
    
    else:
        form = easy_standardtestcaseForm()
        return render(request, 'easy_standardtestcase/post_new.html', {'form': form})