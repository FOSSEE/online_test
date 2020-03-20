from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.contrib import messages
from grades.forms import GradingSystemForm, GradeRangeForm
from grades.models import GradingSystem, GradeRange


@login_required
def grading_systems(request):
    user = request.user
    default_grading_system = GradingSystem.objects.get(name='default')
    grading_systems = GradingSystem.objects.filter(creator=user)
    return render(request, 'grading_systems.html', {'default_grading_system':
                  default_grading_system, 'grading_systems': grading_systems})


@login_required
def add_grading_system(request, system_id=None):
    user = request.user
    grading_system = None
    if system_id is not None:
        grading_system = GradingSystem.objects.get(id=system_id)
    GradeRangeFormSet = inlineformset_factory(GradingSystem, GradeRange,
                                              GradeRangeForm, extra=0)
    grade_form = GradingSystemForm(instance=grading_system)
    is_default = (grading_system is not None and
                  grading_system.name == 'default')

    if request.method == 'POST':
        formset = GradeRangeFormSet(request.POST, instance=grading_system)
        grade_form = GradingSystemForm(request.POST, instance=grading_system)
        if grade_form.is_valid():
            grading_system = grade_form.save(commit=False)
            grading_system.creator = user
            grading_system.save()
            system_id = grading_system.id
            if formset.is_valid():
                formset.save()
            messages.success(request, "Grading system saved successfully")
        if 'add' in request.POST:
            GradeRangeFormSet = inlineformset_factory(
                GradingSystem, GradeRange, GradeRangeForm, extra=1
                )
    formset = GradeRangeFormSet(instance=grading_system)

    return render(request, 'add_grades.html',
                  {'formset': formset,
                   'grade_form': grade_form, "system_id": system_id,
                   'is_default': is_default}
                  )
