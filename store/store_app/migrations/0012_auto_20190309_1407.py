# Generated by Django 2.1.7 on 2019-03-09 14:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store_app', '0011_auto_20190309_1345'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='shippingcons',
            options={'verbose_name': 'партия-перевозка', 'verbose_name_plural': 'партии-перевозки'},
        ),
        migrations.AlterModelOptions(
            name='storagecons',
            options={'verbose_name': 'партия-склад', 'verbose_name_plural': 'партии-склады'},
        ),
        migrations.RemoveField(
            model_name='storagecons',
            name='shipping',
        ),
        migrations.AddField(
            model_name='storagecons',
            name='consignment',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='store_app.Consignment', verbose_name='партия'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='shippingcons',
            name='consignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_app.Consignment', verbose_name='партия'),
        ),
        migrations.AlterField(
            model_name='shippingcons',
            name='shipping',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_app.Shipping', verbose_name='перевозка'),
        ),
        migrations.AlterField(
            model_name='storagecons',
            name='store',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store_app.Store', verbose_name='склад'),
        ),
    ]
