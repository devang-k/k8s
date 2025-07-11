# Generated by Django 5.1.3 on 2025-05-08 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ProjectManager', '0020_alter_techfilecatalog_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='techfilecatalog',
            name='drc_count',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='techfilecatalog',
            name='lvs_count',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='techfilecatalog',
            name='status',
            field=models.CharField(blank=True, choices=[('QUEUED', 'Queued'), ('RUNNING', 'Running'), ('FAILED', 'Failed'), ('COMPLETED', 'Completed'), ('DELETED', 'Deleted'), ('UNPROCESSED', 'Unprocessed')], max_length=11, null=True),
        ),
    ]
