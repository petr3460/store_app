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
            inserted_id = self.objects.insert(self)
            return inserted_id

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

    def __init__(self, id=None, brand=None, carrying=None, owner=None, busy=False):
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

    def __init__(self, id=None, in_process=False, finished=False, created_at=None, finished_at=None, car_id=None, destination_id=None, source_id=None):
        self.id = id
        self.car_id = car_id
        self.source_id = source_id
        self.destination_id = destination_id
        self.in_process = in_process
        self.finished = finished
        self.created_at = created_at
        self.finished_at = finished_at

    def _get_bids(self):
        cursor = connection.cursor()

        query = """SELECT * FROM store_app_bid
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
        products = [Product.get(bid.product_id) for bid in bids]
        car = Car.get(self.car_id)
        carrying = car.carrying * 1000 #перевод килограммов в граммы
        bid_weight = sum([products[i].weight * bids[i].quantity for i in range(len(bids))])
        return carrying >= bid_weight


    def _check_goods_source_enough(self):
        goods_enough = True
        source_store = Store.get(self.source_id)
        bids = self._get_bids()
        bid_goods = {Product.get(b.product_id): b.quantity for b in bids}
        for good, quantity in bid_goods.items():
            cursor = connection.cursor()
            query = '''
                SELECT
                    "store_app_storagecons"."id",
                    "store_app_storagecons"."consignment_id",
                    "store_app_storagecons"."store_id"
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

            total_in_store = sum(Consignment.get(i.consignment_id).quantity for i in storage)  # количество конкретного товара на складе
            if total_in_store < quantity:
                goods_enough = False
        return goods_enough


    def clean(self):
        if self.in_process:
            if not self._check_goods_source_enough():
                raise Exception('На складе-отправителе не достаточно товара')

            if not self._check_fits_in_car():
                raise Exception('Выбранная машина не вмещает весь товар, указанный в заявках')


    def save(self, *args, **kwargs):
        if self.id == None:
            self.created_at = timezone.now()
        self.clean()
        if self.finished:
            cursor = connection.cursor()
            query = '''
                SELECT * FROM store_app_shippingcons WHERE shipping_id = {0};
            '''.format(self.id)
            cursor.execute(query)
            goods = []
            for row in cursor.fetchall():
                s = ShippingCons(*row)
                goods.append(s)
            destination_id = self.destination_id
            for i in goods:
                storage = StorageCons()
                storage.store_id = destination_id
                storage.consignment_id = i.consignment_id
                storage.save()
            self.finished_at = timezone.now()
            car = Car.get(self.car_id)
            car.busy = False
            car.save()
            self.in_process = False

        else:
            car = Car.get(self.car_id)
            car.busy = True
            car.save()

        if self.in_process:
            source_store = self.source_id
            cursor = connection.cursor()
            query = '''
                    SELECT * FROM store_app_bid WHERE shipping_id = {0};
                '''.format(self.id)
            cursor.execute(query)
            bids = []
            for row in cursor.fetchall():
                b = Bid(*row)
                bids.append(b)

            bid_goods = {Product.get(b.product_id): b.quantity for b in bids}

            for good, quantity in bid_goods.items():
                cursor = connection.cursor()
                query = '''
                       SELECT "store_app_storagecons"."id",
                            "store_app_storagecons"."consignment_id",
                            "store_app_storagecons"."store_id" 
                       FROM "store_app_storagecons"
                       INNER JOIN
                       "store_app_consignment" ON ("store_app_storagecons"."consignment_id" = "store_app_consignment"."id")
                       WHERE
                       ("store_app_consignment"."expired" = False
                       AND
                       "store_app_consignment"."product_id" = {0}
                       AND
                       "store_app_storagecons"."store_id" = {1})
                                '''.format(good.id, source_store)
                cursor.execute(query)
                storage = []                        #хранение партий
                for row in cursor.fetchall():
                    s = StorageCons(*row)
                    storage.append(s)

                consignments = [Consignment.get(st_cons.consignment_id) for st_cons in storage] #партии нужного товара на складе
                for cons in consignments:
                    if cons.quantity < quantity:
                        quantity -= cons.quantity
                        new_cons = Consignment()
                        new_cons.product_id = cons.product_id
                        new_cons.manufacture_date = cons.manufacture_date
                        new_cons.quantity = cons.quantity
                        cons.quantity = 0
                        new_cons.cost = cons.cost
                        new_cons_id = new_cons.save()
                        cons.save()
                        ship_cons = ShippingCons()  # новое движение товара
                        ship_cons.consignment_id = new_cons_id
                        ship_cons.shipping_id = self.id
                        ship_cons.save()
                    else:
                        cons.quantity -= quantity
                        new_cons = Consignment()
                        new_cons.product_id = cons.product_id
                        new_cons.manufacture_date = cons.manufacture_date
                        new_cons.quantity = quantity
                        new_cons.cost = cons.cost
                        new_cons_id = new_cons.save()
                        cons.save()
                        ship_cons = ShippingCons()  #новое движение товара
                        ship_cons.consignment_id = new_cons_id
                        ship_cons.shipping_id = self.id
                        ship_cons.save()
        super(Shipping, self).save(*args, **kwargs)


# #  партия
class Consignment(Model):
    class Meta:
        db_table = 'store_app_consignment'

    def __init__(self, id=None, manufacture_date=None, expired=False, cost=None, quantity=None, initial_quantity=None, product_id=None,):
        self.id = id
        self.manufacture_date = manufacture_date
        self.expired = expired
        self.cost = cost
        self.quantity = quantity
        self.initial_quantity = initial_quantity
        self.product_id = product_id


    def save(self, *args, **kwargs):
        if self.id is None:
            self.initial_quantity = self.quantity
            self.manufacture_date = timezone.now()

        inserted_id = super(Consignment, self).save(*args, **kwargs)
        return inserted_id


class ShippingCons(Model):
    class Meta:
        db_table = 'store_app_shippingcons'

    def __init__(self, id=None, consignment_id=None, shipping_id=None):
        self.id = id
        self.consignment_id = consignment_id
        self.shipping_id = shipping_id



class StorageCons(Model):
    class Meta:
        db_table = 'store_app_storagecons'

    def __init__(self, id=None, consignment_id=None, store_id=None):
        self.id = id
        self.consignment_id = consignment_id
        self.store_id = store_id


class Bid(Model):
    class Meta:
        db_table = 'store_app_bid'

    def __init__(self, id=None, quantity=None, product_id=None, shipping_id=None):
        self.id = id
        self.quantity = quantity
        self.product_id = product_id
        self.shipping_id = shipping_id


class UtilShipping(Model):
    class Meta:
        db_table = 'store_app_utilshipping'

    def __init__(self, id=None, finished=False, car_id=None, store_id=None):
        self.id = id
        self.car_id = car_id
        self.store_id = store_id
        self.finished = finished

    def _check_fits_in_car(self, consignments):
        car = Car.get(self.car_id)
        carrying = car.carrying * 1000 #перевод килограммов в граммы
        bid_weight = sum([Product.get(cons.product_id).weight * cons.quantity for cons in consignments])
        return carrying >= bid_weight

    def clean(self):
        if not self.finished:
            mark_expired_products()
            cursor = connection.cursor()
            query = '''
                   SELECT "store_app_storagecons"."id",
                        "store_app_storagecons"."consignment_id",
                        "store_app_storagecons"."store_id" 
                    FROM "store_app_storagecons"
                   INNER JOIN
                   "store_app_consignment" ON ("store_app_storagecons"."consignment_id" = "store_app_consignment"."id")
                   WHERE
                   ("store_app_consignment"."expired" = True
                   AND
                   "store_app_consignment"."quantity" != 0
                   AND
                   "store_app_storagecons"."store_id" = {0})
                            '''.format(self.store_id)
            cursor.execute(query)
            storage = []  # хранение партий
            for row in cursor.fetchall():
                s = StorageCons(*row)
                storage.append(s)
            consignments = [Consignment.get(st_cons.consignment_id) for st_cons in storage]

            if not consignments:
                raise Exception('На складе нет просроченного товара')

            if not self._check_fits_in_car(consignments):
                raise Exception('Весь просроченный товар не влезет в эту машину')

    def save(self, *args, **kwargs):
        if self.finished:
            car = Car.get(self.car_id)
            car.busy = False
            car.save()

        else:
            try:
                self.clean()
            except Exception as e:
                raise e

            car = Car.get(self.car_id)
            car.busy = True
            car.save()
            cursor = connection.cursor()
            query = '''
                   SELECT "store_app_storagecons"."id",
                            "store_app_storagecons"."consignment_id",
                            "store_app_storagecons"."store_id" 
                    FROM "store_app_storagecons"
                   INNER JOIN
                   "store_app_consignment" ON ("store_app_storagecons"."consignment_id" = "store_app_consignment"."id")
                   WHERE
                   ("store_app_consignment"."expired" = True

                   AND
                   "store_app_storagecons"."store_id" = {0})
                            '''.format(self.store_id)
            cursor.execute(query)
            storage = []  # хранение партий
            for row in cursor.fetchall():
                s = StorageCons(*row)
                storage.append(s)

            consignments = [Consignment.get(st_cons.consignment_id) for st_cons in storage]

            for cons in consignments:
                cons.quantity = 0;
                cons.save()
        inserted_id = super(UtilShipping, self).save(*args, **kwargs)
        return inserted_id




def mark_expired_products():
    consignments = Consignment.all()
    was_expired = False
    for cons in consignments:
        product = Product.get(cons.product_id)
        expiration = product.expiration
        if (cons.manufacture_date < (timezone.now() - datetime.timedelta(hours=expiration))) and cons.expired == False:
            cons.expired = True
            cons.save()
            was_expired = True
    return was_expired