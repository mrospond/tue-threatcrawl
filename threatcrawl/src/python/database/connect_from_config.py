from .database_connection import DatabaseConnection
from .data_api import DataAPI


def create_api_from_config(db_config):
    """Creates an instance of the DataAPI class from configuration values

    Parameters
    ----------
    db_config: dict
        A dictionary containing the configuration values for the database connection

    Returns
    -------
    DataAPI
        A DatAPI instance created with the provided settings
    """
    username = db_config['username']
    password = db_config['password']
    host = db_config['host']
    port = db_config['port']
    auth_database = db_config['authorization_database']

    connection = DatabaseConnection(username, password, host, port, auth_database)
    api = DataAPI(connection)

    return api
