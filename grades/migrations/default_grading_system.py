from django.db import migrations


def create_default_system(apps, schema_editor):
    GradingSystem = apps.get_model('grades', 'GradingSystem')
    GradeRange = apps.get_model('grades', 'GradeRange')
    db = schema_editor.connection.alias

    default_system = GradingSystem.objects.using(db).create(name='default')

    graderanges_objects = [
        GradeRange(system=default_system, lower_limit=0, upper_limit=40,
                   grade='F', description='Fail'),
        GradeRange(system=default_system, lower_limit=40, upper_limit=55,
                   grade='P', description='Pass'),
        GradeRange(system=default_system, lower_limit=55, upper_limit=60,
                   grade='C', description='Average'),
        GradeRange(system=default_system, lower_limit=60, upper_limit=75,
                   grade='B', description='Satisfactory'),
        GradeRange(system=default_system, lower_limit=75, upper_limit=90,
                   grade='A', description='Good'),
        GradeRange(system=default_system, lower_limit=90, upper_limit=101,
                   grade='A+', description='Excellent')
    ]
    GradeRange.objects.using(db).bulk_create(graderanges_objects)


def delete_default_system(apps, schema_editor):
    GradingSystem = apps.get_model('grades', 'GradingSystem')
    GradeRange = apps.get_model('grades', 'GradeRange')
    db = schema_editor.connection.alias

    default_system = GradingSystem.objects.using(db).get(creator=None)
    GradeRange.object.using(db).filter(system=default_system).delete()
    default_system.delete()


class Migration(migrations.Migration):
    dependencies = [('grades', '0001_initial'), ]
    operations = [migrations.RunPython(create_default_system,
                  delete_default_system), ]
