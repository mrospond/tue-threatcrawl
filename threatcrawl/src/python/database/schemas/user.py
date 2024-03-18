from database.common import DataType

"""Structure of the user collection

This collection will store all user accounts encountered on any platform.

A schema must have the following properties:
    - collection: str with the name of the collection
    - properties: dict with structure of the data in the collection
"""

user_schema = {
    'properties': {
        'username': {
            'type': DataType.STRING
        },
        'email': {
            'type': DataType.STRING,
            'required': False
        }
    },
    'collection': 'users'
}
