from database.common import DataType

"""Structure of the platform collection

The platform collection will store information about online platforms

A schema must have the following properties:
    - collection: str with the name of the collection
    - properties: dict with structure of the data in the collection
"""

platform_schema = {
    'properties': {
        'name': {
            'type': DataType.STRING
        },
        'url': {
            'type': DataType.STRING,
            'required': False
        },
        'platform_structure_id': {
            'type': DataType.OBJECTID,
            'required': False
        }
    },
    'collection': 'platforms'
}
