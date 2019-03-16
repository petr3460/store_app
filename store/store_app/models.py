from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime


def mark_expired_products():

    consignments = Consignment.objects.all()
    was_expired = False
    for cons in consignments:
        expiration = cons.product.expiration
        if (cons.manufacture_date < (timezone.now() - datetime.timedelta(hours=expiration))) and cons.expired == False:
            cons.expired = True
            cons.save()
            was_expired = True
    return was_expired


class Product(models.Model):
    class Meta:
        verbose_name = "продукт"
        verbose_name_plural = "продукты"

    name = models.CharField(max_length=256, verbose_name='название')
    vendor_code = models.CharField(max_length=256, verbose_name='артикул')
    expiration = models.FloatField(verbose_name='срок годности')
    weight = models.FloatField(verbose_name='масса')
    def __str__(self):
        return self.name


# class CarManager(models.Manager):
#     def get_queryset(self):
#         return super(CarManager, self).get_queryset().filter(busy=False)


class Car(models.Model):
    class Meta:
        verbose_name = "машина"
        verbose_name_plural = "машины"

    def __str__(self):
        return self.brand

    brand = models.CharField(max_length=64, verbose_name='марка')
    carrying = models.FloatField(verbose_name='грузоподъемность')
    owner = models.CharField(max_length=128, verbose_name='владелец')
    busy = models.BooleanField(default=False, blank=True, verbose_name='занята')
    # objects = CarManager()


class Store(models.Model):
    class Meta:
        verbose_name = "склад"
        verbose_name_plural = "склады"

    def __str__(self):
        return self.name
    owner = models.CharField(max_length=128, verbose_name='владелец')
    name = models.CharField(max_length=32, verbose_name='название')
    capacity = models.IntegerField(verbose_name='вместимость')



class Shipping(models.Model):
    class Meta:
        verbose_name = "перевозка"
        verbose_name_plural = "перевозки"

    car = models.ForeignKey(Car, on_delete=models.CASCADE, verbose_name='машина')
    source = models.ForeignKey(Store, blank=False, on_delete=models.CASCADE, verbose_name='отправление', related_name='source')
    destination = models.ForeignKey(Store, blank=False, on_delete=models.CASCADE, verbose_name='назначение', related_name='destination')
    in_process = models.BooleanField(default=False, blank=True, verbose_name='выполняется')
    finished = models.BooleanField(default=False, blank=True, verbose_name='выполнена')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='создана')
    finished_at = models.DateTimeField(verbose_name='выполнена', blank=True, null=True)

    def __str__(self):
        return str(self.created_at.ctime()) + ' from ' + self.source.name + ' to ' + self.destination.name

    def _check_fits_in_car(self):
        bids = self.bid_set.all()
        carrying = self.car.carrying * 1000 #перевод килограммов в граммы
        bid_weight = sum([bid.product.weight * bid.quantity for bid in bids])
        # import pdb
        # pdb.set_trace()
        return carrying >= bid_weight


    def _check_goods_source_enough(self):
        source_store = self.source
        bids = self.bid_set.all()
        bid_goods = {b.product: b.quantity for b in bids}
        for good, quantity in bid_goods.items():
            mark_expired_products()
            storage = StorageCons.objects.filter(store=source_store, consignment__expired=False, consignment__product=good)  # хранение партий
            total_in_store = sum(i.consignment.quantity for i in storage)  # количество конкретного товара на складе
            if total_in_store < quantity:
                return False
            else:
                return True

    def clean(self):
        print('run clean')
        if self.in_process:
            if not self._check_goods_source_enough():
                raise ValidationError('На складе-отправителе не достаточно товара')

            if not self._check_fits_in_car():
                raise ValidationError('Выбранная машина не вмещает весь товар, указанный в заявках')

    def save(self, *args, **kwargs):
        print('run save')
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
            # for good, quantity in bid_goods.items():
            #     storage = StorageCons.objects.filter(store=source_store, consignment__product=good) #хранение партий
            #     total_in_store = sum(i.consignment.quantity for i in storage)   #количество конкретного товара на складе
            #     if total_in_store < quantity:
            #         self.in_process = False
            # if self.in_process: # если товара хватает

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

#  партия
class Consignment(models.Model):
    class Meta:
        verbose_name = "партия товара"
        verbose_name_plural = "партии товара"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='продукт')
    manufacture_date = models.DateTimeField(verbose_name='дата изготовления')
    expired = models.BooleanField(blank=True, default=False, verbose_name='просрочен')
    cost = models.FloatField(verbose_name='цена')
    quantity = models.IntegerField(verbose_name='количество')
    initial_quantity = models.IntegerField(verbose_name='изначальное количество', blank=True, null=True)

    def __str__(self):
        return self.product.name + ' : ' + str(self.quantity)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.initial_quantity = self.quantity
        super(Consignment, self).save(*args, **kwargs)


class ShippingCons(models.Model):
    class Meta:
        verbose_name = "движение товара"
        verbose_name_plural = "движения товара"

    shipping = models.ForeignKey(Shipping, on_delete=models.CASCADE, verbose_name='перевозка')
    consignment = models.OneToOneField(Consignment, on_delete=models.CASCADE, verbose_name='партия')

    def __str__(self):
        return '#' + str(self.id) + ' ' + \
               self.consignment.product.name + ':  ' +\
               self.shipping.source.name + ' -> ' +\
               self.shipping.destination.name



class StorageCons(models.Model):
    class Meta:
        verbose_name = "хранение товара"
        verbose_name_plural = "хранение товара"

    def __str__(self):
        return self.store.name + ' : ' + self.consignment.product.name + ' : ' + str(self.consignment.quantity)

    store = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name='склад')
    consignment = models.OneToOneField(Consignment, on_delete=models.CASCADE, verbose_name='партия')


class Bid(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='продукт')
    quantity = models.IntegerField(verbose_name='количество')
    shipping = models.ForeignKey(Shipping, on_delete=models.CASCADE, verbose_name='перевозка')

    class Meta:
        unique_together = ("product", "shipping")
        verbose_name = "заявка на перевозку"
        verbose_name_plural = "заявки на перевозку"

    def __str__(self):
        return '#' + str(self.id) + ' ' + \
               self.product.name + ':  ' + str(self.quantity)


class UtilShipping(models.Model):

    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    finished = models.BooleanField(default=False, blank=True)

    class Meta:
        verbose_name = "Утилизация"
        verbose_name_plural = "Утилизационные перевозки"

    def __str__(self):
        return '#' + str(self.id) + self.store.name + ' -> ' + ('finished' if self.finished else '')

    def _check_fits_in_car(self, consignments):
        carrying = self.car.carrying * 1000 #перевод килограммов в граммы
        bid_weight = sum([cons.product.weight * cons.quantity for cons in consignments])

        return carrying >= bid_weight

    def clean(self):
        if not self.finished:
            mark_expired_products()
            storage = StorageCons.objects.filter(store=self.store, consignment__expired=True)  # хранение партий
            consignments = [st_cons.consignment for st_cons in storage]
            if not consignments:
                raise ValidationError('На складе нет просроченного товара')

            if not self._check_fits_in_car(consignments):
                raise ValidationError('Весь просроченный товар не влезет в эту машину')

    def save(self, *args, **kwargs):
        if self.finished:
            self.car.busy = False

        else:
            self.car.busy = True
            storage = StorageCons.objects.filter(store=self.store, consignment__expired=True)  # хранение партий
            consignments = [st_cons.consignment for st_cons in storage]


            for cons in consignments:
                cons.quantity = 0;
                cons.save()
        super(UtilShipping, self).save(*args, **kwargs)

