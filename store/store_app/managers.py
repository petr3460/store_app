from django.db import connection


class ProductManager():
    def __init__(self):
        pass

    
    # @staticmethod
    # def format_boolean(value):
    #     return 'TRUE' if value else 'FALSE'
    #
    # @staticmethod
    # def format_date(value):
    #     return value.isoformat()
    #
    # @staticmethod
    # def format_datetime(value):
    #     return value.isoformat()

    @staticmethod
    def delete(c):
        pass

    @staticmethod
    def update(c):
        cursor = connection.cursor()
        attributes = ''
        for a in c.__dict__.keys():
            attributes += a + "='" + str(c.__dict__[a]) + "',"
        if attributes[-1] == ',':
            attributes = attributes[:-1]

        query = """UPDATE {0}
                   SET {1}
                   WHERE id={2};""".format(
            c.Meta.db_table,
            attributes,
            c.id)
        print('run query: ' + query)
        cursor.execute(query)

    @staticmethod
    def insert(obj):
        cursor = connection.cursor()
        attr_names = [a for a in obj.__dict__.keys() if a != 'id']
        attr_names_str = ','.join(attr_names)
        attr_values = [obj.__dict__.get(k) for k in attr_names]
        attr_values_str = ','.join("'{}'".format(str(v)) for v in attr_values)
        query = """INSERT INTO {0}
                   ({1})
                   VALUES ({2});""".format(
            obj.Meta.db_table,
            attr_names_str,
            attr_values_str)

        cursor.execute(query)

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