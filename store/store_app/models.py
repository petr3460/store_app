from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
from .managers import ProductManager
from django.db import connection


class Model:
    def __init__(self):
        pass

    objects = ProductManager()

    def save(self):
        if self.id is not None:
            self.objects.update(self)
        else:
            self.objects.insert(self)

    def delete(self):
        self.objects.delete(self)

    @classmethod
    def all(cls):
        return cls.objects.all(cls)

    @classmethod
    def get(cls, id):
        return cls.objects.get(cls, id)



class Product(Model):
    class Meta:
        db_table = 'store_app_product'

    def __init__(self, id=None, name=None, vendor_code=None, expiration=None, weight=None):
        self.id = id
        self.name = name
        self.vendor_code = vendor_code
        self.expiration = expiration
        self.weight = weight


class Car(Model):
    class Meta:
        db_table = 'store_app_car'

    def __init__(self, id=None, brand=None, carrying=None, owner=None, busy=None):
        self.id = id
        self.brand = brand
        self.carrying = carrying
        self.owner = owner
        self.busy = busy



class Store(Model):
    class Meta:
        db_table = 'store_app_store'

    def __init__(self, id=None, owner=None, name=None, capacity=None):
        self.id = id
        self.owner = owner
        self.name = name
        self.capacity = capacity


class Shipping(Model):
    class Meta:
        db_table = 'store_app_shipping'

    def __init__(self, id=None, car=None, source=None, destination=None, in_process=False, finished=False, created_at=None, finished_at=None):
        self.id = id
        self.car = car
        self.source = source
        self.destination = destination
        self.in_process = in_process
        self.finished = finished
        self.created_at = created_at
        self.finished_at = finished_at

    def _get_bids(self):
        cursor = connection.cursor()

        query = """SELECT * FROM 'store_app_bid'
                   WHERE shipping_id={0};""".format(
                    self.id)

        cursor.execute(query)
        bids = []

        for row in cursor.fetchall():
            b = Bid(*row)
            bids.append(b)

        return bids


    def _check_fits_in_car(self):

        bids = self._get_bids()
        products = [Product.objects.get(bid.product_id) for bid in bids]

        car = Car.objects.get(self.car)
        carrying = car.carrying * 1000 #перевод килограммов в граммы
        bid_weight = sum([products[i].weight * bids[i].quantity for i in range(len(bids))])
        return carrying >= bid_weight

    def _check_goods_source_enough(self):
        goods_enough = True
        source_store = Store.objects.get(self.source)
        bids = self._get_bids()
        bid_goods = {Product.objects.get(b.product): b.quantity for b in bids}
        for good, quantity in bid_goods.items():
            # mark_expired_products()

            cursor = connection.cursor()
            query = '''
                SELECT
                    "store_app_storagecons"."id",
                    "store_app_storagecons"."store_id",
                    "store_app_storagecons"."consignment_id"
                FROM
                    "store_app_storagecons"
                INNER JOIN
                    "store_app_consignment"
                ON
                    ("store_app_storagecons"."consignment_id" = "store_app_consignment"."id")
                WHERE
                    ("store_app_consignment"."expired" = False
                AND
                    "store_app_consignment"."product_id" = {0}
                AND
                    "store_app_storagecons"."store_id" = {1}
                )
            '''.format(good.id, source_store.id)
            cursor.execute(query)
            storage = []    # хранение партий

            for row in cursor.fetchall():
                s = StorageCons(*row)
                storage.append(s)

            total_in_store = sum(Consignment.objects.get(i.consignment).quantity for i in storage)  # количество конкретного товара на складе
            if total_in_store < quantity:
                goods_enough = False

        return goods_enough


    def clean(self):
        if self.in_process:
            if not self._check_goods_source_enough():
                raise Exception('На складе-отправителе не достаточно товара')

            if not self._check_fits_in_car():
                raise Exception('Выбранная машина не вмещает весь товар, указанный в заявках')


# -------------ОСТАНОВИЛСЯ ЗДЕСЬ-------------------
    def save(self, *args, **kwargs):
        self.clean()
        if self.finished:
            goods = self.shippingcons_set.all()
            destination_id = self.destination
            for i in goods:
                storage = StorageCons()
                storage.store = destination_id
                storage.consignment = i.consignment
                storage.save()
            self.finished_at = timezone.now()
            self.car.busy = False
            self.in_process = False
            self.car.save()
        else:
            self.car.busy = True
            self.car.save()

        if self.in_process:
            source_store = self.source
            bids = self.bid_set.all()
            bid_goods = {b.product: b.quantity for b in bids}

            for good, quantity in bid_goods.items():
                storage = StorageCons.objects.filter(store=source_store, consignment__product=good) #хранение партий
                consignments = [st_cons.consignment for st_cons in storage] #партии нужного товара на складе
                for cons in consignments:
                    if cons.quantity < quantity:
                        quantity -= cons.quantity
                        new_cons = Consignment()
                        new_cons.product = cons.product
                        new_cons.manufacture_date = cons.manufacture_date
                        new_cons.quantity = cons.quantity
                        cons.quantity = 0
                        new_cons.cost = cons.cost
                        new_cons.save()
                        cons.save()
                        ship_cons = ShippingCons()  # новое движение товара
                        ship_cons.consignment = new_cons
                        ship_cons.shipping = self
                        ship_cons.save()
                    else:
                        cons.quantity -= quantity
                        new_cons = Consignment()
                        new_cons.product = cons.product
                        new_cons.manufacture_date = cons.manufacture_date
                        new_cons.quantity = quantity
                        new_cons.cost = cons.cost
                        new_cons.save()
                        cons.save()
                        ship_cons = ShippingCons()  #новое движение товара
                        ship_cons.consignment = new_cons
                        ship_cons.shipping = self
                        ship_cons.save()
        super(Shipping, self).save(*args, **kwargs)
#
#
#
# class Shipping(models.Model):
#     class Meta:
#         verbose_name = "перевозка"
#         verbose_name_plural = "перевозки"
#
#     car = models.ForeignKey(Car, on_delete=models.CASCADE, verbose_name='машина')
#     source = models.ForeignKey(Store, blank=False, on_delete=models.CASCADE, verbose_name='отправление', related_name='source')
#     destination = models.ForeignKey(Store, blank=False, on_delete=models.CASCADE, verbose_name='назначение', related_name='destination')
#     in_process = models.BooleanField(default=False, blank=True, verbose_name='выполняется')
#     finished = models.BooleanField(default=False, blank=True, verbose_name='выполнена')
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name='создана')
#     finished_at = models.DateTimeField(verbose_name='выполнена', blank=True, null=True)
#
#     def __str__(self):
#         return str(self.created_at.ctime()) + ' from ' + self.source.name + ' to ' + self.destination.name
#
#     def _check_fits_in_car(self):
#         bids = self.bid_set.all()
#         carrying = self.car.carrying * 1000 #перевод килограммов в граммы
#         bid_weight = sum([bid.product.weight * bid.quantity for bid in bids])
#         return carrying >= bid_weight
#
#
#     def _check_goods_source_enough(self):
#         source_store = self.source
#         bids = self.bid_set.all()
#         bid_goods = {b.product: b.quantity for b in bids}
#         for good, quantity in bid_goods.items():
#             mark_expired_products()
#             storage = StorageCons.objects.filter(store=source_store, consignment__expired=False, consignment__product=good)  # хранение партий
#             total_in_store = sum(i.consignment.quantity for i in storage)  # количество конкретного товара на складе
#             if total_in_store < quantity:
#                 return False
#             else:
#                 return True
#
#     def clean(self):
#         print('run clean')
#         if self.in_process:
#             if not self._check_goods_source_enough():
#                 raise ValidationError('На складе-отправителе не достаточно товара')
#
#             if not self._check_fits_in_car():
#                 raise ValidationError('Выбранная машина не вмещает весь товар, указанный в заявках')
#
#     def save(self, *args, **kwargs):
#         print('run save')
#         if self.finished:
#             goods = self.shippingcons_set.all()
#             destination_id = self.destination
#             for i in goods:
#                 storage = StorageCons()
#                 storage.store = destination_id
#                 storage.consignment = i.consignment
#                 storage.save()
#             self.finished_at = timezone.now()
#             self.car.busy = False
#             self.in_process = False
#             self.car.save()
#         else:
#             self.car.busy = True
#             self.car.save()
#
#         if self.in_process:
#             source_store = self.source
#             bids = self.bid_set.all()
#             bid_goods = {b.product: b.quantity for b in bids}
#
#             for good, quantity in bid_goods.items():
#                 storage = StorageCons.objects.filter(store=source_store, consignment__product=good) #хранение партий
#                 consignments = [st_cons.consignment for st_cons in storage] #партии нужного товара на складе
#                 for cons in consignments:
#                     if cons.quantity < quantity:
#                         quantity -= cons.quantity
#                         new_cons = Consignment()
#                         new_cons.product = cons.product
#                         new_cons.manufacture_date = cons.manufacture_date
#                         new_cons.quantity = cons.quantity
#                         cons.quantity = 0
#                         new_cons.cost = cons.cost
#                         new_cons.save()
#                         cons.save()
#                         ship_cons = ShippingCons()  # новое движение товара
#                         ship_cons.consignment = new_cons
#                         ship_cons.shipping = self
#                         ship_cons.save()
#                     else:
#                         cons.quantity -= quantity
#                         new_cons = Consignment()
#                         new_cons.product = cons.product
#                         new_cons.manufacture_date = cons.manufacture_date
#                         new_cons.quantity = quantity
#                         new_cons.cost = cons.cost
#                         new_cons.save()
#                         cons.save()
#                         ship_cons = ShippingCons()  #новое движение товара
#                         ship_cons.consignment = new_cons
#                         ship_cons.shipping = self
#                         ship_cons.save()
#         super(Shipping, self).save(*args, **kwargs)
#
#
# #  партия
# class Consignment(models.Model):
#     class Meta:
#         verbose_name = "партия товара"
#         verbose_name_plural = "партии товара"
#
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='продукт')
#     manufacture_date = models.DateTimeField(verbose_name='дата изготовления')
#     expired = models.BooleanField(blank=True, default=False, verbose_name='просрочен')
#     cost = models.FloatField(verbose_name='цена')
#     quantity = models.IntegerField(verbose_name='количество')
#     initial_quantity = models.IntegerField(verbose_name='изначальное количество', blank=True, null=True)
#
#     def __str__(self):
#         return self.product.name + ' : ' + str(self.quantity)
#
#     def save(self, *args, **kwargs):
#         if not self.pk:
#             self.initial_quantity = self.quantity
#         super(Consignment, self).save(*args, **kwargs)
#
#
# class ShippingCons(models.Model):
#     class Meta:
#         verbose_name = "движение товара"
#         verbose_name_plural = "движения товара"
#
#     shipping = models.ForeignKey(Shipping, on_delete=models.CASCADE, verbose_name='перевозка')
#     consignment = models.OneToOneField(Consignment, on_delete=models.CASCADE, verbose_name='партия')
#
#     def __str__(self):
#         return '#' + str(self.id) + ' ' + \
#                self.consignment.product.name + ':  ' +\
#                self.shipping.source.name + ' -> ' +\
#                self.shipping.destination.name
#
#
#
# class StorageCons(models.Model):
#     store = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name='склад')
#     consignment = models.OneToOneField(Consignment, on_delete=models.CASCADE, verbose_name='партия')
#
#     class Meta:
#         verbose_name = "хранение товара"
#         verbose_name_plural = "хранение товара"
#
#     def __str__(self):
#         return self.store.name + ' : ' + self.consignment.product.name + ' : ' + str(self.consignment.quantity)
#
#
# class Bid(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='продукт')
#     quantity = models.IntegerField(verbose_name='количество')
#     shipping = models.ForeignKey(Shipping, on_delete=models.CASCADE, verbose_name='перевозка')
#
#     class Meta:
#         unique_together = ("product", "shipping")
#         verbose_name = "заявка на перевозку"
#         verbose_name_plural = "заявки на перевозку"
#
#     def __str__(self):
#         return '#' + str(self.id) + ' ' + \
#                self.product.name + ':  ' + str(self.quantity)
#
#
# class UtilShipping(models.Model):
#
#     car = models.ForeignKey(Car, on_delete=models.CASCADE)
#     store = models.ForeignKey(Store, on_delete=models.CASCADE)
#     finished = models.BooleanField(default=False, blank=True)
#
#     class Meta:
#         verbose_name = "Утилизация"
#         verbose_name_plural = "Утилизационные перевозки"
#
#     def __str__(self):
#         return '#' + str(self.id) + self.store.name + ' -> ' + ('finished' if self.finished else '')
#
#     def _check_fits_in_car(self, consignments):
#         carrying = self.car.carrying * 1000 #перевод килограммов в граммы
#         bid_weight = sum([cons.product.weight * cons.quantity for cons in consignments])
#
#         return carrying >= bid_weight
#
#     def clean(self):
#         if not self.finished:
#             mark_expired_products()
#             storage = StorageCons.objects.filter(store=self.store, consignment__expired=True)  # хранение партий
#             consignments = [st_cons.consignment for st_cons in storage]
#             if not consignments:
#                 raise ValidationError('На складе нет просроченного товара')
#
#             if not self._check_fits_in_car(consignments):
#                 raise ValidationError('Весь просроченный товар не влезет в эту машину')
#
#     def save(self, *args, **kwargs):
#         if self.finished:
#             self.car.busy = False
#
#         else:
#             self.car.busy = True
#             storage = StorageCons.objects.filter(store=self.store, consignment__expired=True)  # хранение партий
#             consignments = [st_cons.consignment for st_cons in storage]
#
#
#             for cons in consignments:
#                 cons.quantity = 0;
#                 cons.save()
#         super(UtilShipping, self).save(*args, **kwargs)
#



# def mark_expired_products():
#     consignments = Consignment.objects.all()
#     was_expired = False
#     for cons in consignments:
#         expiration = cons.product.expiration
#         if (cons.manufacture_date < (timezone.now() - datetime.timedelta(hours=expiration))) and cons.expired == False:
#             cons.expired = True
#             cons.save()
#             was_expired = True
#     return was_expired