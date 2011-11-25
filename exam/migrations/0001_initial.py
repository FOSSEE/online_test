# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Profile'
        db.create_table('exam_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('roll_number', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('institute', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('department', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('position', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('exam', ['Profile'])

        # Adding model 'Question'
        db.create_table('exam_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('points', self.gf('django.db.models.fields.FloatField')(default=1.0)),
            ('test', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('options', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=24)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('exam', ['Question'])

        # Adding model 'Answer'
        db.create_table('exam_answer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['exam.Question'])),
            ('answer', self.gf('django.db.models.fields.TextField')()),
            ('error', self.gf('django.db.models.fields.TextField')()),
            ('marks', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('correct', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('exam', ['Answer'])

        # Adding model 'Quiz'
        db.create_table('exam_quiz', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('start_date', self.gf('django.db.models.fields.DateField')()),
            ('duration', self.gf('django.db.models.fields.IntegerField')(default=20)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('exam', ['Quiz'])

        # Adding model 'QuestionPaper'
        db.create_table('exam_questionpaper', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['exam.Profile'])),
            ('quiz', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['exam.Quiz'])),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('user_ip', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('questions', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('questions_answered', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('comments', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('exam', ['QuestionPaper'])

        # Adding M2M table for field answers on 'QuestionPaper'
        db.create_table('exam_questionpaper_answers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('questionpaper', models.ForeignKey(orm['exam.questionpaper'], null=False)),
            ('answer', models.ForeignKey(orm['exam.answer'], null=False))
        ))
        db.create_unique('exam_questionpaper_answers', ['questionpaper_id', 'answer_id'])


    def backwards(self, orm):
        
        # Deleting model 'Profile'
        db.delete_table('exam_profile')

        # Deleting model 'Question'
        db.delete_table('exam_question')

        # Deleting model 'Answer'
        db.delete_table('exam_answer')

        # Deleting model 'Quiz'
        db.delete_table('exam_quiz')

        # Deleting model 'QuestionPaper'
        db.delete_table('exam_questionpaper')

        # Removing M2M table for field answers on 'QuestionPaper'
        db.delete_table('exam_questionpaper_answers')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'exam.answer': {
            'Meta': {'object_name': 'Answer'},
            'answer': ('django.db.models.fields.TextField', [], {}),
            'correct': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'error': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['exam.Question']"})
        },
        'exam.profile': {
            'Meta': {'object_name': 'Profile'},
            'department': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institute': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'roll_number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'exam.question': {
            'Meta': {'object_name': 'Question'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'options': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'points': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'test': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '24'})
        },
        'exam.questionpaper': {
            'Meta': {'object_name': 'QuestionPaper'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'answers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['exam.Answer']", 'symmetrical': 'False'}),
            'comments': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['exam.Profile']"}),
            'questions': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'questions_answered': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'quiz': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['exam.Quiz']"}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user_ip': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'exam.quiz': {
            'Meta': {'object_name': 'Quiz'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'default': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['exam']
