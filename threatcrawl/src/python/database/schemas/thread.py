from database.common import DataType

"""Structure of the thread collection

This collection will store all threads that have crawled.

A schema must have the following properties:
    - collection: str with the name of the collection
    - properties: dict with structure of the data in the collection
"""

thread_schema = {
    'properties': {
        # Thread title
        'title': {
            'type': DataType.STRING
        },
        # id of the platform hosting the thread
        'platform_id': {
            'type': DataType.OBJECTID
        },
        # The relevance level of the thread
        'relevancy': {
            'type': DataType.RELEVANCE
        },
        # A list of id's to all the (parsed) posts in the thread
        'posts': {
            'type': DataType.OBJECTID,
            'isArray': True
        }
    },
    'collection': 'threads'
}
