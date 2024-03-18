"""
This module contains the schema definitions for the document collections in the database.
"""
from .configuration import config_schema
from .platform_structure import platform_structure_schema
from .platform import platform_schema
from .post import post_schema
from .raw_data import raw_data_schema
from .thread import thread_schema
from .user import user_schema
from .workday import workday_schema
from .resource_identifier import resource_identifier_schema
from .full_webpage import full_webpage_schema

schemas = [config_schema, full_webpage_schema, platform_schema, platform_structure_schema,
           post_schema, raw_data_schema, thread_schema, user_schema, workday_schema,
           resource_identifier_schema]
