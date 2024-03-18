from database.common import DataType


"""Structure of the post collection

The post collection will store users posts from any platform or thread.

A schema must have the following properties:
    - collection: str with the name of the collection
    - properties: dict with structure of the data in the collection
"""

attachments = {
    'type': DataType.OBJECTID,
    'isArray': True,
}

post_schema = {
    'properties': {
        # For the n-th post in the thread, the sequence_number is n
        'sequence_number': {
            'type': DataType.INT32
        },
        # The content of the post
        'content': {
            'type': DataType.STRING,
            'required': False
        },
        # A list of attachments, if any are available
        'attachments': attachments,
        # The date at which the post was posted
        'date_posted': {
            'type': DataType.STRING, # DataType.DATE
            'required': False
        },
        # A reference to the thread of the post
        'thread_id': {
            'type': DataType.OBJECTID
        },
        # A reference to the author of the post
        'user_id': {
            'type': DataType.OBJECTID
        }
    },
    'collection': 'posts'
}
