import json
from pathlib import Path


def write_webpage_from_id(api, id):
    document = api['full webpage'].find_by_id(id).include_file('folder_contents').exec()

    if document is None:
        raise RuntimeWarning(f'There is no webpage with id={id}, cannot write webpage to file.')

    write_webpage_from_document(document)


def write_webpage_from_document(document):
    """Takes a document containing a web page and writes it to disk

    Parameters
    ----------
    document: dict
        The document that contains a full webpage
    """
    path = Path('~/Documents/' + document['file_name'] + '/').expanduser()
    folder_path = path / Path(document['file_name'] + '_files/')

    try:
        Path(folder_path).mkdir(parents=True, exist_ok=True)
    except OSError:
        print(f'Creation of the directories "{path}" and "{folder_path}" failed')

    # write webpage files to disk
    print('Writing assets...')
    for file_name, file_contents in zip(document['folder_names'], document['folder_contents']):
        with open(folder_path / file_name, 'wb') as file:
            file.write(file_contents)

    # write HTML page to disk
    print('writing index.html...')
    with open(path / 'index.html', 'w', encoding='utf-8') as file:
        file.write(document['file_contents'])

    print('Finished!')


def class_attributes(class_name):
    """Lists the values of all the public class attributes

    Parameters
    ----------
    class_name: str
        The name of the class

    Returns
    -------
    list of any
        The values of the public class attributes of `class_name`
    """
    return [getattr(class_name, value) for value in dir(class_name) if not value.startswith('__')]


def is_binary_type(data):
    """Returns whether the data is of a binary data type"""
    return type(data) in [bytes, bytearray]


def replace_values(document, path, replacer=lambda x: x):
    """Replaces values in the document at the specified path

    The function takes a document and a path and will replace
    all values on the path in the document. The replacement is
    provided by a function (replacer), which is called with the
    original value. The return value of the function is then used
    as a replacement.

    Parameters
    ----------
    document: any
        The document which contains values that shall be replaced
    path: list of str
        The location of the values that shall be replaced. Each property
        of the path should be an element in the list, so for
        example: ['thread', 'posts', 'author'].
    replacer: function(any): any
        The function that provides the replacements for values
    """
    property = path.pop(0)

    if type(document) is dict and property in document:
        if len(path) == 0:
            document[property] = replacer(document[property])
        else:
            replace_values(document[property], path.copy(), replacer)
        return

    if type(document) is list:
        for element in document:
            if type(element) is dict and property in element:
                if len(path) == 0:
                    element[property] = replacer(element[property])
                else:
                    replace_values(element[property], path.copy(), replacer)


def pretty_print(object):
    """Pretty prints an object and its attributes

    Takes an object and prints all the attributes that it has
    in a recursive manner.

    Parameters
    ----------
    object: any
        The object to be pretty-printed

    Returns
    -------
    str
        A string containing a printed version of the object
    """
    return json.dumps(object, indent=4, default=lambda o: getattr(o, '__dict__', str(o)))


def to_json(object):
    """Prints an object and its attributes to a string

    Takes an object and prints all the attributes that it has
    in a recursive manner.

    Parameters
    ----------
    object: any
        The object to be printed

    Returns
    -------
    str
        A string containing a printed version of the object
    """
    return json.dumps(object, default=lambda o: getattr(o, '__dict__', str(o)))
