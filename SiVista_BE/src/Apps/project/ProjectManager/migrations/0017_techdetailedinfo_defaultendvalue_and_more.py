# Generated by Django 5.1.3 on 2025-04-09 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ProjectManager', '0016_alter_techdetailedinfo_stepper'),
    ]

    operations = [
        migrations.AddField(
            model_name='techdetailedinfo',
            name='defaultEndValue',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='techdetailedinfo',
            name='defaultStartValue',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='techdetailedinfo',
            name='endPercentage',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='techdetailedinfo',
            name='maxEnd',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='techdetailedinfo',
            name='maxStart',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='techdetailedinfo',
            name='minEnd',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='techdetailedinfo',
            name='minStart',
            field=models.IntegerField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='techdetailedinfo',
            name='startPercentage',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
