# Generated by Django 2.1.7 on 2019-02-26 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store_app', '0002_auto_20190224_2026'),
    ]

    operations = [
        migrations.AddField(
            model_name='consignment',
            name='status',
            field=models.CharField(choices=[('transit', 'в пути'), ('storage', 'хранение'), ('expired', 'просрочен')], default='storage', max_length=64),
        ),
    ]