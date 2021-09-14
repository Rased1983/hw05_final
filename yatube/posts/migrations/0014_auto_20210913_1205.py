# Generated by Django 2.2.16 on 2021-09-13 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_auto_20210913_1112'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='unique following',
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='%(app_label)s_%(class)s_name_unique'),
        ),
    ]
