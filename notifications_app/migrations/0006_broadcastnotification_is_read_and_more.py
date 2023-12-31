# Generated by Django 4.0 on 2023-11-11 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications_app', '0005_remove_broadcastnotification_is_read_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='broadcastnotification',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='broadcastnotification',
            name='broadcast_on',
            field=models.DateTimeField(),
        ),
    ]
