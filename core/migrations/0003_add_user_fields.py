from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_assignment_assignmentitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='class_section',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='roll_number',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='teacher_id',
            field=models.CharField(max_length=150, null=True, blank=True),
        ),
    ]
