from enums import CaptchaType
from enums import Relevance
from enums import PageType


class DataType:
    """Supported MongoDB datatypes

    MongoDB supports custom enumerations, such as "Relevance". If you wish to add a custom enumeration,
    just adding it here suffices.

    Notes
    -----
    ARRAY is for internal use only. In validation schemas, use the "isArray" option to indicate if
    something is an array or not.

    The same holds for TIMESTAMP, so never use it. Use DATE instead.
    """
    DOUBLE = 'double'
    STRING = 'string'
    OBJECT = 'object'
    ARRAY = 'array'
    BINARY_DATA = 'binData'
    OBJECTID = 'objectId'
    BOOLEAN = 'bool'
    DATE = 'date'
    NULL = 'null'
    REGULAR_EXPRESSION = 'regex'
    JAVASCRIPT = 'javascript'
    INT32 = 'int'
    TIMESTAMP = 'timestamp'
    INT64 = 'long'
    DECIMAL = 'decimal'
    MIN_KEY = 'minKey'
    MAX_KEY = 'maxKey'
    RELEVANCE = Relevance
    CAPTCHA_TYPE = CaptchaType
    PAGE_TYPE = PageType
