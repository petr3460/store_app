from django import forms
from .models import *


class ProductForm(forms.Form):
    name = forms.CharField(label='Название продукта', max_length=100)
    vendor_code = forms.CharField(label='артикул', max_length=20)
    expiration = forms.IntegerField(label='срок годности (ч)')
    weight = forms.FloatField(label='вес (г)')


class CarForm(forms.Form):
    brand = forms.CharField(label='Марка', max_length=20)
    carrying = forms.IntegerField(label='Грузоподъемность (кг)')
    owner = forms.CharField(label='Владелец', max_length=50)


class StoreForm(forms.Form):
    owner = forms.CharField(label='Владелец', max_length=50)
    name = forms.CharField(label='Название склада', max_length=100)
    capacity = forms.IntegerField(label='Вместимость (т)')


class ShippingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ShippingForm, self).__init__(*args, **kwargs)
        CARS = tuple((c.id, c.brand) for c in Car.all() if c.busy == False)
        self.fields['car_id'] = forms.ChoiceField(choices=CARS, label='Машина')
        STORES = tuple((s.id, s.name) for s in Store.all())
        self.fields['source_id'] = forms.ChoiceField(choices=STORES, label='Отправление')
        self.fields['destination_id'] = forms.ChoiceField(choices=STORES, label='Назначение')


class ConsignmentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ConsignmentForm, self).__init__(*args, **kwargs)
        PRODUCTS = tuple((p.id, p.name) for p in Product.all())
        self.fields['product_id'] = forms.ChoiceField(choices=PRODUCTS, label='Продукт')

    cost = forms.FloatField(label='Цена')
    quantity = forms.IntegerField(label='Количество')


class ShippingConsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ShippingConsForm, self).__init__(*args, **kwargs)
        SHIPPINGS = tuple((s.id, s.id) for s in Shipping.all())
        self.fields['shipping_id'] = forms.ChoiceField(choices=SHIPPINGS, label='Перевозка')
        CONSIGNMENTS = tuple((c.id, c.id) for c in Consignment.all())
        self.fields['consignment_id'] = forms.ChoiceField(choices=CONSIGNMENTS, label='Партия')


class StorageConsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(StorageConsForm, self).__init__(*args, **kwargs)
        STORES = tuple((s.id, s.name) for s in Store.all())
        self.fields['store_id'] = forms.ChoiceField(choices=STORES, label='Склад')
        CONSIGNMENTS = tuple((c.id, c.id) for c in Consignment.all())
        self.fields['consignment_id'] = forms.ChoiceField(choices=CONSIGNMENTS, label='Партия')


class BidForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BidForm, self).__init__(*args, **kwargs)
        SHIPPINGS = tuple((s.id, s.id) for s in Shipping.all())
        self.fields['shipping_id'] = forms.ChoiceField(choices=SHIPPINGS, label='Перевозка')
        PRODUCTS = tuple((p.id, p.name) for p in Product.all())
        self.fields['product_id'] = forms.ChoiceField(choices=PRODUCTS, label='Продукт')

    quantity = forms.IntegerField(label='Количество')


class UtilShippingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(UtilShippingForm, self).__init__(*args, **kwargs)
        CARS = tuple((c.id, c.brand) for c in Car.all() if c.busy == False)
        self.fields['car_id'] = forms.ChoiceField(choices=CARS, label='Машина')
        STORES = tuple((s.id, s.name) for s in Store.all())
        self.fields['store_id'] = forms.ChoiceField(choices=STORES, label='Склад')




