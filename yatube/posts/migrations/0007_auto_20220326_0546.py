# Generated by Django 2.2.16 on 2022-03-26 05:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_follow'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/'),
        ),
    ]
