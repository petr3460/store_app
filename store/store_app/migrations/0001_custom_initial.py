from django.db import migrations

sql_query = '''
BEGIN;

CREATE TABLE "store_app_bid" ("id" serial NOT NULL PRIMARY KEY, "quantity" integer NOT NULL);

CREATE TABLE "store_app_car" ("id" serial NOT NULL PRIMARY KEY, "brand" varchar(64) NOT NULL, "carrying" double precision NOT NULL, "owner" varchar(128) NOT NULL, "busy" boolean NOT NULL);

CREATE TABLE "store_app_consignment" ("id" serial NOT NULL PRIMARY KEY, "manufacture_date" timestamp with time zone NOT NULL, "expired" boolean NOT NULL, "cost" double precision NOT NULL, "quantity" integer NOT NULL, "initial_quantity" integer NULL);

CREATE TABLE "store_app_product" ("id" serial NOT NULL PRIMARY KEY, "name" varchar(256) NOT NULL, "vendor_code" varchar(256) NOT NULL, "expiration" double precision NOT NULL, "weight" double precision NOT NULL);

CREATE TABLE "store_app_shipping" ("id" serial NOT NULL PRIMARY KEY, "in_process" boolean NOT NULL, "finished" boolean NOT NULL, "created_at" timestamp with time zone NOT NULL, "finished_at" timestamp with time zone NULL, "car_id" integer NOT NULL);

CREATE TABLE "store_app_shippingcons" ("id" serial NOT NULL PRIMARY KEY, "consignment_id" integer NOT NULL UNIQUE, "shipping_id" integer NOT NULL);

CREATE TABLE "store_app_storagecons" ("id" serial NOT NULL PRIMARY KEY, "consignment_id" integer NOT NULL UNIQUE);

CREATE TABLE "store_app_store" ("id" serial NOT NULL PRIMARY KEY, "owner" varchar(128) NOT NULL, "name" varchar(32) NOT NULL, "capacity" integer NOT NULL);

CREATE TABLE "store_app_utilshipping" ("id" serial NOT NULL PRIMARY KEY, "finished" boolean NOT NULL, "car_id" integer NOT NULL, "store_id" integer NOT NULL);

ALTER TABLE "store_app_storagecons" ADD COLUMN "store_id" integer NOT NULL;

ALTER TABLE "store_app_shipping" ADD COLUMN "destination_id" integer NOT NULL;

ALTER TABLE "store_app_shipping" ADD COLUMN "source_id" integer NOT NULL;

ALTER TABLE "store_app_consignment" ADD COLUMN "product_id" integer NOT NULL;

ALTER TABLE "store_app_bid" ADD COLUMN "product_id" integer NOT NULL;

ALTER TABLE "store_app_bid" ADD COLUMN "shipping_id" integer NOT NULL;

ALTER TABLE "store_app_bid" ADD CONSTRAINT "store_app_bid_product_id_shipping_id_5cdd26c9_uniq" UNIQUE ("product_id", "shipping_id");
ALTER TABLE "store_app_shipping" ADD CONSTRAINT "store_app_shipping_car_id_6a714484_fk_store_app_car_id" FOREIGN KEY ("car_id") REFERENCES "store_app_car" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "store_app_shipping_car_id_6a714484" ON "store_app_shipping" ("car_id");
ALTER TABLE "store_app_shippingcons" ADD CONSTRAINT "store_app_shippingco_consignment_id_9f946102_fk_store_app" FOREIGN KEY ("consignment_id") REFERENCES "store_app_consignment" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "store_app_shippingcons" ADD CONSTRAINT "store_app_shippingco_shipping_id_9fe7ae02_fk_store_app" FOREIGN KEY ("shipping_id") REFERENCES "store_app_shipping" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "store_app_shippingcons_shipping_id_9fe7ae02" ON "store_app_shippingcons" ("shipping_id");
ALTER TABLE "store_app_storagecons" ADD CONSTRAINT "store_app_storagecon_consignment_id_46b6ed05_fk_store_app" FOREIGN KEY ("consignment_id") REFERENCES "store_app_consignment" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "store_app_utilshipping" ADD CONSTRAINT "store_app_utilshipping_car_id_8a1e8983_fk_store_app_car_id" FOREIGN KEY ("car_id") REFERENCES "store_app_car" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "store_app_utilshipping" ADD CONSTRAINT "store_app_utilshipping_store_id_b0ee2b76_fk_store_app_store_id" FOREIGN KEY ("store_id") REFERENCES "store_app_store" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "store_app_utilshipping_car_id_8a1e8983" ON "store_app_utilshipping" ("car_id");
CREATE INDEX "store_app_utilshipping_store_id_b0ee2b76" ON "store_app_utilshipping" ("store_id");
CREATE INDEX "store_app_storagecons_store_id_d582f13a" ON "store_app_storagecons" ("store_id");
ALTER TABLE "store_app_storagecons" ADD CONSTRAINT "store_app_storagecons_store_id_d582f13a_fk_store_app_store_id" FOREIGN KEY ("store_id") REFERENCES "store_app_store" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "store_app_shipping_destination_id_57740039" ON "store_app_shipping" ("destination_id");
ALTER TABLE "store_app_shipping" ADD CONSTRAINT "store_app_shipping_destination_id_57740039_fk_store_app" FOREIGN KEY ("destination_id") REFERENCES "store_app_store" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "store_app_shipping_source_id_74250e67" ON "store_app_shipping" ("source_id");
ALTER TABLE "store_app_shipping" ADD CONSTRAINT "store_app_shipping_source_id_74250e67_fk_store_app_store_id" FOREIGN KEY ("source_id") REFERENCES "store_app_store" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "store_app_consignment_product_id_57dbd91a" ON "store_app_consignment" ("product_id");
ALTER TABLE "store_app_consignment" ADD CONSTRAINT "store_app_consignmen_product_id_57dbd91a_fk_store_app" FOREIGN KEY ("product_id") REFERENCES "store_app_product" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "store_app_bid_product_id_eff9209d" ON "store_app_bid" ("product_id");
ALTER TABLE "store_app_bid" ADD CONSTRAINT "store_app_bid_product_id_eff9209d_fk_store_app_product_id" FOREIGN KEY ("product_id") REFERENCES "store_app_product" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "store_app_bid_shipping_id_3a6a173b" ON "store_app_bid" ("shipping_id");
ALTER TABLE "store_app_bid" ADD CONSTRAINT "store_app_bid_shipping_id_3a6a173b_fk_store_app_shipping_id" FOREIGN KEY ("shipping_id") REFERENCES "store_app_shipping" ("id") DEFERRABLE INITIALLY DEFERRED;
COMMIT;
'''

class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(sql_query),
    ]
