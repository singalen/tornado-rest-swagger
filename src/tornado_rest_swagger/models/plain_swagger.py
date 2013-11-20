

class PlainModelReader(object):
    """
    Reads a Swagger-compatible model description from a plain Python object instance.
    TODO: Add some metadata convention for min/max/etc, probably
    """

    def __init__(self):
        super(PlainModelReader, self).__init__()

    @staticmethod
    def read(clazz):
        obj = clazz()

        members = {
            attr: {
                "type": type_name(type(getattr(obj, attr))),
                #"$ref": "Category", - TODO
                #"format": "int64",
                #"description": "Unique identifier for the Pet",
                #"minimum": "0.0",
                #"maximum": "100.0"
            }
            for attr in dir(obj)
            if not callable(attr) and not attr.startswith("__")
        }

        return {
            'id': clazz.__name__,
            'description': (clazz.__doc__ or '').strip(),
            'properties': members,
        }

def type_name(typ):
    """
    Python data type to Swagger type
    """
    name = typ.__name__
    if name == 'str' or name == 'unicode':
        return 'string'
    elif name == 'int':
        return 'integer'
    elif name == 'bool':
        return 'boolean'
    elif name == 'list' or name == 'set':
        return 'array'

    return name
