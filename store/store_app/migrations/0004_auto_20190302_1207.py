# Generated by Django 2.1.7 on 2019-03-02 12:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store_app', '0003_consignment_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storage',
            name='consignment',
        ),
        migrations.RemoveField(
            model_name='storage',
            name='store',
        ),
        migrations.RemoveField(
            model_name='consignment',
            name='status',
        ),
        migrations.AddField(
            model_name='consignment',
            name='shipping',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='store_app.Shipping'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='consignment',
            name='storage',
            field=models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='store_app.Store'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shipping',
            name='car',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='store_app.Car'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shipping',
            name='destination',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='store_app.Store'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Storage',
        ),
    ]