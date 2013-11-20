import tornado_rest_swagger.models.plain_swagger


def _type_to_swagger(alchemy_type):
    return tornado_rest_swagger.models.plain_swagger.type_name(alchemy_type.python_type)


def _attr_type(attr):
    return _type_to_swagger(attr.property.columns[0].type)


class SqlAlchemyModelReader(object):
    """
    A little ball of mud that reads a Swagger-compatible model description from a SqlAlchemy class.
    """

    def __init__(self):
        super(SqlAlchemyModelReader, self).__init__()


    @staticmethod
    def read(clazz):
        required_cols = []

        fields = {
            name: {
                "type": _attr_type(attr),
                #"format": "int64",
                'description': '',
                #"minimum": "0.0",
                #"maximum": "100.0"
                'required': hasattr(attr.property.columns[0], 'required'),
                'column': iter(attr.property.columns).next().expression,
            }
            for name, attr in dict(clazz.__dict__).items()
            if hasattr(attr, 'is_attribute') and attr.is_attribute and hasattr(attr.property, 'columns')
        }

        one_to_manies = {
            name: {
                'type': 'array',
                'items': {'$ref': attr.property.mapper.class_.__name__}
            }
            for name, attr in clazz.__dict__.items()
            if name != 'metalist' and hasattr(attr, 'property') and hasattr(attr.property, 'target') and 'ONETOMANY' in str(attr.property.direction)
        }

        table_columns = [field['column'] for name, field in fields.items()]
        many_to_ones = {
            name: {
                "$ref": attr.property.mapper.class_.__name__,
                #"format": "int64",
                'description': '',
                #"minimum": "0.0",
                #"maximum": "100.0"
                #'required': attr._orig_columns[0].required TODO:
                'column': iter(attr.property.local_columns).next().expression,
            }
            for name, attr in clazz.__dict__.items()
            if hasattr(attr, 'property') and hasattr(attr.property, 'target') and 'MANYTOONE' in str(attr.property.direction)
        }

        many_to_ones = {name: field for name, field in many_to_ones.items() if field['column'] not in table_columns}

        all_properties = dict(fields.items() + one_to_manies.items() + many_to_ones.items())
        for k, v in all_properties.items():
            if 'column' in v:
                del v['column']

        return {
            'id': clazz.__name__,
            'description': (clazz.__doc__ or '').strip(),
            'properties': all_properties,
            'required': required_cols
        }