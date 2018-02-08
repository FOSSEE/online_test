from django.db import migrations

def create_default_system(apps, schema_editor):
    GradingSystem = apps.get_model('grades', 'GradingSystem')
    GradeRange = apps.get_model('grades', 'GradeRange')
    db = schema_editor.connection.alias

    default_system = GradingSystem.objects.using(db).create(name='default',
                                                           can_be_used=True)
    GradeRange.objects.using(db).create(system=default_system, order=1, lower_limit=0,
                              upper_limit=40, grade='F', description='Fail')
    GradeRange.objects.using(db).create(system=default_system, order=2, lower_limit=40,
                              upper_limit=55, grade='P', description='Pass')
    GradeRange.objects.using(db).create(system=default_system, order=3, lower_limit=55,
                              upper_limit=60, grade='C', description='Average')
    GradeRange.objects.using(db).create(system=default_system, order=4, lower_limit=60,
                              upper_limit=75, grade='B', description='Satisfactory')
    GradeRange.objects.using(db).create(system=default_system, order=5, lower_limit=75,
                              upper_limit=90, grade='A', description='Good')
    GradeRange.objects.using(db).create(system=default_system, order=6, lower_limit=90,
                              upper_limit=101, grade='A+', description='Excellent')


def delete_default_system(apps, schema_editor):
    GradingSystem = apps.get_model('grades', 'GradingSystem')
    GradeRange = apps.get_model('grades', 'GradeRange')
    db = schema_editor.connection.alias

    default_system = GradingSystem.objects.using(db).get(creator=None)
    GradeRange.object.using(db).filter(system=default_system).delete()
    default_system.delete()


class Migration(migrations.Migration):
    dependencies = [('grades', '0001_initial'),]
    operations = [migrations.RunPython(create_default_system, delete_default_system),]
