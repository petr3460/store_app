from django.db import connection


class ProductManager():
    def __init__(self):
        pass


    @staticmethod
    def delete(c):
        pass

    @staticmethod
    def update(obj):
        cursor = connection.cursor()
        attributes = ''
        for a in obj.__dict__.keys():
            attributes += a + "={},".format("'{}'".format(obj.__dict__[a]) if obj.__dict__[a] != None else "NULL")
        if attributes[-1] == ',':
            attributes = attributes[:-1]
        query = """UPDATE {0}
                   SET {1}
                   WHERE id={2};""".format(
            obj.Meta.db_table,
            attributes,
            obj.id)
        print('run query: ' + query)
        cursor.execute(query)


    @staticmethod
    def insert(obj):
        cursor = connection.cursor()
        attr_names = [a for a in obj.__dict__.keys() if a != 'id']
        attr_names_str = ','.join(attr_names)
        attr_values = [obj.__dict__.get(k) for k in attr_names]
        attr_values_str = ','.join("{}".format("'{}'".format(str(v)) if v != None else "NULL") for v in attr_values)
        query = """INSERT INTO {0}
                   ({1})
                   VALUES ({2})
                   RETURNING id;""".format(
            obj.Meta.db_table,
            attr_names_str,
            attr_values_str)
        print('run query: ' + query)
        cursor.execute(query)
        inserted_id = cursor.fetchone()[0]
        return inserted_id


    @staticmethod
    def all(cls):
        cursor = connection.cursor()
        query = """SELECT *
                  FROM {0};""".format(
                    cls.Meta.db_table
        )
        cursor.execute(query)
        objects = []
        for row in cursor.fetchall():
            c = cls(*row)
            objects.append(c)
        return objects


    @staticmethod
    def get(cls, id):
        cursor = connection.cursor()
        query = """SELECT *
                   FROM {0}
                   WHERE id={1};""".format(
                        cls.Meta.db_table,
                        id)
        cursor.execute(query)
        objects = []
        for row in cursor.fetchall():
            c = cls(*row)
            objects.append(c)
        return None if len(objects) == 0 else objects[0]