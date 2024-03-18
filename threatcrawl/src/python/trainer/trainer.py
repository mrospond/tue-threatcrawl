"""File containing the Trainer class."""
from collections import Counter
from time import sleep

import pymsgbox
from selenium.common.exceptions import InvalidSelectorException
from selenium.webdriver.common.by import By
from tbselenium.tbdriver import TorBrowserDriver

from trainer.analyzer_method1 import AnalyzerMethod1
from trainer.analyzer_method4 import AnalyzerMethod4
from trainer.page_structure import PageStructure
from trainer.html_element import HTMLElement
from tld import get_tld
from trainer.analyzer_method2 import AnalyzerMethod2
from trainer.analyzer_method3 import AnalyzerMethod3
from trainer.html_class import HTMLClass
from trainer.xpath import XPath
from trainer.xpath_except import XPathExcept
from enums import NavigationalElement, DataElement, InputElement, PageType
from database.util import to_json
from trainer.xpath_injector import XPathInjector
from utils import Logger
import websockets
import asyncio
import json
from enum import Enum


class Trainer:
    """Trainer class for the trainer module.

    The Trainer class communicates with the database, GUI and crawler in order to retrieve resource identifiers
    for different structural elements from the database, and construct them if necessary.

    Attributes
    ----------
    gui_port : int
        The GUI port number.
    """

    def __init__(self, data_api, gui_port = 8080, driver: TorBrowserDriver = None, had_issues = [],
                 method_identifiers_map = None):
        """Initialize the Trainer.

        Parameters
        ----------
        data_api : DataAPI
            The API for communicating with the database.
        gui_port : int
            The port number on which the GUI is listening for incoming data.
        """
        if method_identifiers_map is None:
            self.method_identifiers_map = {}
        else:
            self.method_identifiers_map = method_identifiers_map

        self.data_api = data_api
        self.gui_port = gui_port
        self.driver = driver

        # Analyzer methods in order of preference
        self.analyzer_methods = [AnalyzerMethod3(), AnalyzerMethod2(),
                                 AnalyzerMethod1(), AnalyzerMethod4(), XPathInjector()]
        self.had_issues = had_issues
        self.tried_selenium = False
        self.first_time_in_session = False
        self.first_time_asked = True
        self.iteration_count = 0
        self.had_issues = had_issues

    def train(self, page, page_type=None, javascript: str = ''):
        """Train the crawler on a web page.

        The trainer receives platform pages from the crawler for training. The trainer then sends the platform page to
        the GUI, and will check whether a page structure of the platform page exists in the database.
        If so, the identifiers are retrieved from the database and sent to the GUI for the user to verify.
        If not, the trainer will construct the identifiers, using user input from the GUI.
        The resulting identifiers are sent to both database and crawler for further usage.

        Parameters
        ----------
        page : Page
            The web page to be trained.
        page_type : PageType, optional
            The page type of the web page; this should be provided when retraining and hence the page type is known.
        javascript : str
            JavaScript to execute in that page.

        Returns
        -------
        PageStructure
            The trained PageStructure for the provided `page`.
        """
        # Get platform url, e.g. https://canvas.tue.nl/courses/14813 becomes canvas.tue.nl
        platform_url = get_tld(page.url, as_object=True).parsed_url.netloc

        # Get page data from database
        page_data = self.get_page_data_from_database(page.url)
        page_data['file_contents'] = page.html
        # Perform training session, this includes all communication with the GUI
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            trained_page_structure = asyncio.get_event_loop().run_until_complete(
                self.perform_training_session(platform_url, page_data, page_type, javascript=javascript))
        except ConnectionRefusedError as e:
            raise ConnectionRefusedError(f"No connection could be made with the websocket of the GUI at port "
                                         f"{self.gui_port}.\nPlease check whether the GUI is running.") from e

        # If there was JS to execute, then communicate that it was not a training yet to the training_sequence.
        if isinstance(trained_page_structure, str):
            return trained_page_structure, self.method_identifiers_map

        # Save trained page structure in database
        self.send_identifiers_to_database(platform_url, trained_page_structure.page_type,
                                          trained_page_structure.identifiers, trained_page_structure.javascript)

        # Return trained page structure
        return trained_page_structure, self.method_identifiers_map

    def construct_identifiers_for_page(self, page_html, identified_elements, ignored_elements, prev_identifiers,
                                       keep_same_method=False):
        """Construct identifiers for a web page.

        Parameters
        ----------
        page_html : str
            The HTML of the web page for which identifiers are constructed.
        identified_elements : dict<key: StructuralElement, value: list of HTMLElement>
            A dictionary where for every structural element on the web page, the identified HTML elements are given.
        ignored_elements : dict<key: StructuralElement, value: list of HTMLElement>
            A dictionary where for every structural element on the web page, the ignored HTML elements are given.
        prev_identifiers : dict<key: StructuralElement, value: ResourceIdentifier or None>
            A dictionary where for every structural element on the web page, the previous identifier is given. Is None
            if no previous identifier is known.
        keep_same_method : bool
            A flag that allows to recalculate the identifiers by using the previously valid AnalyzerMethod for elements
            that don't need retraining.

        Returns
        -------
        dict<key: StructuralElement, value: ResourceIdentifier>
            The ResourceIdentifier for each StructuralElement on the trained web page.
        """
        identifiers = {}
        for k, v in identified_elements.items():
            # This happens for the non-retrained identifiers, allowing to recalculate them but without changing their
            # calculation strategy. However, in the case of incomplete training or other unforeseen issues, it may
            # happen that correctly identified elements are already stored in the database, and for them there's no info
            # about their previous method. Therefore, no method would match. To solve the issue, they will be calculated
            # again. This is suboptimal, because it forces to retrain these elements, whereas it would be sufficient to
            # save the previous ones. However, this would imply that other (questionable) modifications have to be done
            # to this software.
            if self.method_identifiers_map[k] != 0 and keep_same_method:
                if len(prev_identifiers[k]) != 0 and identified_elements[k] == 0:
                    identifiers[k] = prev_identifiers[k][0]
                else:
                    for i, method in enumerate(self.analyzer_methods):
                        if self.method_identifiers_map[k] == i+1:
                            ignored = ignored_elements.get(k, [])
                            identifier_or_none = method.construct_identifier(page_html, v, ignored, k, driver=self.driver)
                            if identifier_or_none is None:
                                identifiers[k] = prev_identifiers[k][0]
                            else:
                                identifiers[k] = identifier_or_none
                            break
            # Regular iterative construction of identifiers
            else:
                if len(prev_identifiers[k]) != 0:
                    # Check previous identifier to return ResourceIdentifier
                    if prev_identifiers[k] is not None and len(prev_identifiers[k]) > 0:
                        identifiers[k] = prev_identifiers[k][0]
                # If there is at least an identifier...
                elif len(v) != 0:
                    found = False
                    ignored = ignored_elements.get(k, [])
                    for i, method in enumerate(self.analyzer_methods):
                        try:
                            if i != len(self.analyzer_methods) - 1:
                                if self.method_identifiers_map[k] > i:
                                    continue
                        except KeyError:
                            # That key wasn't here yet. Let's add it
                            self.method_identifiers_map[k] = 0
                        self.method_identifiers_map[k] = i+1
                        identifier_or_none = method.construct_identifier(page_html, v, ignored, k, driver=self.driver)
                        # If the method yielded something (hence it was a result shown before) but it is not the
                        # one desired, then keep on going with the next method.
                        if identifier_or_none is not None:
                            identifiers[k] = identifier_or_none
                            found = True
                            break
                    if not found:
                        # For now, raise an exception when no resource identifier can be constructed
                        raise Exception("No resource identifier was able to be constructed "
                                        "for the html element: {} of type {}".format(v, k))
                # ...else, there's nothing.
                else:
                    identifiers[k] = None
        return identifiers

    async def perform_training_session(self, platform_url, page_data, page_type, javascript: str = ''):
        """Perform a training session on a web page.

        Parameters
        ----------
        platform_url : str
            The URL of the platform for which a page is trained.
        page_data : Dict[str, Any]
            A dictionary containing the data of a web page from the database.
        page_type : PageType or None
            The type of the web page, None if it is unknown.
        javascript : str
            JavaScript to execute in that page.

        Returns
        -------
        PageStructure
            The trained page structure.
        """
        async with websockets.connect("ws://localhost:" + str(self.gui_port)) as websocket:
            # Open the training screen, and send the page id such that the GUI can fetch page assets from database
            if page_type is not None:
                page_type_name = page_type.name
            else:
                page_type_name = 'None'
            message = {
                'action': 'open training screen',
                'data': page_data['_id'],
                'platform_url': platform_url,
                'page_type': page_type_name
            }
            await websocket.send(to_json(message))

            # Perform training iterations
            page_struct = await self.perform_training_iterations(page_data['file_contents'], websocket, platform_url,
                                                                 javascript_previous=javascript)
        return page_struct

    async def send_web_page_to_gui(self, assets, websocket):
        """Send web page to GUI.

        Parameters
        ----------
        assets : Dict[str, str]
            The asset files and their content which is sent to the GUI.
        websocket : WebSocket
            The WebSocket over which data is sent.
        """
        await websocket.send(to_json(assets))

    async def perform_training_iterations(self, page_html, websocket, platform_url, javascript_previous: str = ''):
        """Perform training iterations until the user confirms the identified structure is correct.

        Parameters
        ----------
        page_html : str
            The HTML of the page to train.
        websocket : WebSocket
            The WebSocket over which data is sent.
        platform_url : str
            The URL of the page to train.
        javascript_previous : str
            JavaScript to execute in that page coming from the previous iteration(s).

        Returns
        -------
        PageStructure
            The trained page structure.
        """
        dct = {}
        # Get input from user. First response should never equal 'structure is correct'.
        response = await websocket.recv()
        Logger.log("trainer", "Received user input")
        identifiers = None
        while response != 'structure is correct':
            if json.loads(response)['javascript'] != '':
                javascript = json.loads(response)['javascript']
                # I'm executing JS and communicating that this was not yet a training, hence go back to the main
                # training sequence to download again the page after executing JS
                self.driver.execute_script(javascript)
                sleep(5)
                return javascript
            else:
                dct = json.loads(response, object_hook=user_input_json_decoder)
                self.verify_and_populate_method_identifiers_map(dct)
                identifiers, compatible_identifiers = self.create_and_identify_selectors(dct, page_html)
            # if iteration_count > 0:
            #     if is_first_training:
            #         for k, v in dct['structural_elements'].items():
            #             dct['structural_elements'][k][2] = v[0]
            #     # if not self.first_time_in_session:
            #     if pymsgbox.confirm('Does the error depend on something you may have clicked "better" or you already '
            #                         'indicated a problem with a specific element caused from THREAT/crawl?',
            #                         'Check', ['Yes', 'No']) == 'No':
            #         incremented_this_round = False
            #         # Those are errors identified from the user, meaning that something has been wrongly highlighted
            #         for key in identifiers.keys():
            #             answer = pymsgbox.confirm('Is the problem with ' + key.name + '?', 'Check', ['Yes', 'No'])
            #             if answer == 'Yes':
            #                 self.method_identifiers_map[key] = self.method_identifiers_map[key] + 1
            #                 self.had_issues.append(key)
            #         identifiers, compatible_identifiers = self.create_and_identify_selectors(dct, page_html)
            await websocket.send(json.dumps({
                'action': 'doublecheck',
                'data': compatible_identifiers
            }, cls=CustomJSONEncoder))
            Logger.log("trainer", "Sent constructed identifiers")

            # Get response from GUI
            response = await websocket.recv()
            Logger.log("trainer", "Received user input")

            self.iteration_count += 1
        Logger.log("trainer", "Received confirmation of structure")
        return PageStructure(dct['page_type'], identifiers, javascript_previous)

    def verify_and_populate_method_identifiers_map(self, dct):
        if self.method_identifiers_map is not {}:
            if self.method_identifiers_map == {}:
                for navigational_item in NavigationalElement:
                    self.method_identifiers_map[navigational_item] = 0
                for data_element in DataElement:
                    self.method_identifiers_map[data_element] = 0
                for input_element in InputElement:
                    self.method_identifiers_map[input_element] = 0

    def create_and_identify_selectors(self, dct, page_html):
        selected_elements = {k: v[0] for k, v in dct['structural_elements'].items()}
        ignored_elements = {k: v[1] for k, v in dct['structural_elements'].items()}
        prev_identifiers = {k: v[2] for k, v in dct['structural_elements'].items()}
        # no_longer_visible_elements = []
        # Meaning: is it the first time we train that page (and therefore we have nothing to compare with yet)?
        has_prev_identifiers = False
        for k, v in prev_identifiers.items():
            if len(v) > 0:
                has_prev_identifiers = True
                break

        if not has_prev_identifiers:
            for k, v in self.method_identifiers_map.items():
                if v != 0:
                    has_prev_identifiers = True
                    break

        if has_prev_identifiers:
            keys = selected_elements.keys()
            for k in keys:
                # TODO This is because for some reason the frontend doesn't send back the previous identifiers. This
                #  should be fixed in the future.
                no_prev_id = False
                if prev_identifiers[k] is None:
                    no_prev_id = True
                elif len(prev_identifiers[k]) == 0:
                    no_prev_id = True
                if no_prev_id and self.method_identifiers_map[k] != 0:
                    for i, method in enumerate(self.analyzer_methods):
                        if self.method_identifiers_map[k] == i + 1:
                            ignored = ignored_elements.get(k, [])
                            v = selected_elements.get(k)
                            identifier_or_none = method.construct_identifier(page_html, v, ignored, k, driver=self.driver)
                            if identifier_or_none is not None:
                                if not isinstance(identifier_or_none, list):
                                    identifier_or_none = [identifier_or_none]
                                prev_identifiers[k] = identifier_or_none
                            break

                if len(prev_identifiers[k]) != 0:
                    if isinstance(prev_identifiers[k][0], XPathExcept):
                        prev_elements = self.driver.find_elements(By.XPATH, prev_identifiers[k][0].x_path_use.x_path)
                        remove = prev_identifiers[k][0].x_path_remove.x_path
                        for remove_elem in remove.split(" | "):
                            try:
                                prev_elements.remove(self.driver.find_elements(By.XPATH, remove_elem)[0])
                            except ValueError:
                                continue
                    else:
                        try:
                            prev_elements = self.driver.find_elements(By.XPATH, prev_identifiers[k][0].x_path)
                        except InvalidSelectorException:
                            prev_elements = []
                        # if len(prev_elements) == 0:
                        #     no_longer_visible_elements.append(prev_identifiers[k][0].x_path)
                    curr_elements = []
                    for elem in selected_elements[k]:
                        curr_elements = curr_elements + self.driver.find_elements(By.XPATH, elem.x_path)
                    if Counter(prev_elements) != Counter(curr_elements):
                        # if self.first_time_asked:
                        #     answer = pymsgbox.confirm('Is this the first time you\'re training on this page during '
                        #                               'this session?', 'Check', ['Yes', 'No'])
                        #     if answer == 'Yes':
                        #         self.first_time_asked = False
                        #         self.first_time_in_session = True
                        #         self.had_issues.append(k)
                        # else:
                        #     if not self.first_time_in_session:
                        answer = pymsgbox.confirm('Did you change ' + k.name + # todo cambia probabilmente questo in qualcosa tipo "hai rimosso?"
                                                  ' because of wrong identification from THREAT/crawl or are you '
                                                  'starting from scratch/you misclicked/there\'s no such '
                                                  'element in this page/you did nothing?', 'Check',
                                                  [k.name + ' problem by THREAT/crawl', 'Ignore'])
                        if answer != 'Ignore':
                            self.had_issues.append(k)

        # We're training for the first time this page (so we have no previous identifiers as reference),
        # and we're adjusting it, or it has been reset during its lifecycle and we're adjusting it.
        elif not has_prev_identifiers and self.iteration_count > 0:
            keys = selected_elements.keys()
            for k in keys:
                answer = pymsgbox.confirm(
                    'Did you change ' + k.name +  # todo cambia probabilmente questo in qualcosa tipo "hai rimosso?"
                    ' because of wrong identification from THREAT/crawl or are you '
                    'starting from scratch/you misclicked/there\'s no such '
                    'element in this page/you did nothing?', 'Check',
                    [k.name + ' problem by THREAT/crawl', 'Ignore'])
                if answer != 'Ignore':
                    self.had_issues.append(k)

        # Did we have any issue so far? By issues, I mean the scenario in which training was ok, but after refreshing
        # the page THREAT/crawl could not identify again the elements (identifier changed). In this scenario, I keep trace of
        # what elements had problems, and I can ask the trainer to use another method.
        if len(self.had_issues) != 0:
            retrain_selected_elements = {k: v[0] for k, v in dct['structural_elements'].items() if k in self.had_issues}
            retrain_ignored_elements = {k: v[1] for k, v in dct['structural_elements'].items() if k in self.had_issues}
            retrain_prev_identifiers = {k: v[2] for k, v in dct['structural_elements'].items() if k in self.had_issues}
            keys = retrain_prev_identifiers.keys()
            for key in keys:
                # If an element had issues, was previously identified but now there's no more, I'll remove it completely
                if len(retrain_selected_elements[key]) == 0:
                    retrain_prev_identifiers[key] = []
            retrained_identifiers = self.construct_identifiers_for_page(
                page_html, retrain_selected_elements, retrain_ignored_elements, retrain_prev_identifiers)
            for key in keys:
                if retrained_identifiers[key] is None:
                    retrained_identifiers.pop(key)
            non_retrained_selected_elements = {k: v[0] for k, v in dct['structural_elements'].items()
                                               if k not in self.had_issues}
            non_retrained_ignored_elements = {k: v[1] for k, v in dct['structural_elements'].items()
                                              if k not in self.had_issues}
            non_retrained_prev_identifiers = {k: v[2] for k, v in dct['structural_elements'].items()
                                              if k not in self.had_issues}
            identifiers = self.construct_identifiers_for_page(
                page_html, non_retrained_selected_elements, non_retrained_ignored_elements,
                non_retrained_prev_identifiers, keep_same_method=True)
            identifiers = {**identifiers, **retrained_identifiers}
        else:
            # Construct resource identifiers for selected elements, and send it to the GUI
            identifiers = self.construct_identifiers_for_page(
                page_html, selected_elements, ignored_elements, prev_identifiers, keep_same_method=True)
        for struct_elmnt, res_identifier in identifiers.items():
            try:
                res_identifier.date_format = dct['structural_elements'][struct_elmnt][3]
            except AttributeError:
                continue

        # self.first_time_in_session = False
        compatible_identifiers = _make_identifiers_json_compatible(identifiers)
        return identifiers, compatible_identifiers

    async def send_page_structure_to_gui(self, page_structure, websocket):
        """Send page structure to GUI.

        Parameters
        ----------
        page_structure : PageStructure
            The identifiers of the structural elements that are known.
        websocket : WebSocket
            The WebSocket over which the `page_structure` is sent.

        """
        if page_structure is not None:
            identifiers_json = self.convert_page_structure_to_json(page_structure)
        else:
            identifiers_json = "{ }"
        await websocket.send(identifiers_json)

    def convert_page_structure_to_json(self, page_structure):
        """Convert page structure to JSON format.

        Parameters
        ----------
        page_structure : PageStructure
            The identifiers of the structural elements that are known.

        Returns
        -------
        str
            String of the JSON representation of `page_structure`.
        """
        structure_dict = page_structure.__dict__
        json_dict = structure_dict.copy()
        json_dict['identifiers'] = _make_identifiers_json_compatible(json_dict['identifiers'])

        return json.dumps(json_dict, cls=CustomJSONEncoder)

    def get_page_structure_from_database(self, platform_url, page_type):
        """Get the identifiers of a given page type on a platform from the database.

        Parameters
        ----------
        platform_url : str
            The URL of the platform.
        page_type : PageType
            The page type to return identifiers for, such as FrontPage or LoginPage.

        Returns
        -------
        PageStructure
            The page structure stored in the database for this `platform_url` and `page_type`.
        """
        url_identifiers = self.get_identifiers_from_database(platform_url, page_type)
        return PageStructure(page_type, url_identifiers, javascript="")

    def get_identifiers_from_database(self, platform_url, page_type):
        """Get the identifiers of a given page type on a platform from the database.

        Parameters
        ----------
        platform_url : str
            The URL of the platform.
        page_type : PageType
            The page type to return identifiers for, such as FrontPage or LoginPage.

        Returns
        -------
        dict<key: StructuralElement, value: ResourceIdentifier>
            The ResourceIdentifier for each StructuralElement that is in the database for the provided page type and
            platform. If there is no corresponding ResourceIdentifier in database for a certain StructuralElement,
            then this key is not present in the dictionary.
        """
        url_identifiers = {}
        docu_identifiers = self.data_api['resource identifier'].find_one(
            {
                'platform_url': platform_url,
                'page_type': page_type,
            }).exec()

        if docu_identifiers is None:
            return url_identifiers

        structural_elements = docu_identifiers['structural_elements']
        for structural_element, identifier_dict in structural_elements.items():
            date_format = identifier_dict['date_format']
            if identifier_dict['identifier_type'] == "XPath":
                xpath = identifier_dict['identifier']
                url_identifiers[convert_name_to_structural_element(structural_element)] = \
                    XPath(xpath, date_format=date_format)
            if identifier_dict['identifier_type'] == "HTMLClass":
                html_class = identifier_dict['identifier']
                url_identifiers[convert_name_to_structural_element(structural_element)] = \
                    HTMLClass(html_class, date_format=date_format)
            if identifier_dict['identifier_type'] == "XPathExcept":
                x_path_use = identifier_dict['identifier']['x_path_use']
                x_path_remove = identifier_dict['identifier']['x_path_remove']
                url_identifiers[convert_name_to_structural_element(structural_element)] = \
                    XPathExcept(XPath(x_path_use), XPath(x_path_remove), date_format=date_format)
        return url_identifiers

    def get_page_data_from_database(self, page_url):
        """Get the assets of a given url from the database, this includes things like images and CSS files.

        Parameters
        ----------
        page_url : str
            The URL of the page.

        Returns
        -------
        Dict
            A dictionary containing all data regarding `page_url` from the database.
        """
        return (self.data_api['full webpage']
                .find_one({'page_url': page_url})
                .include_files('folder_contents')
                .exec())

    def send_identifiers_to_database(self, platform_url, page_type, identifiers, javascript):
        """Update the identifiers in the database.

        Parameters
        ----------
        platform_url : str
            The URL of the platform for which the identifiers are updated.
        page_type : PageType
            The type of page for which the identifiers are updated.
        identifiers : dict<key: StructuralElement, value: ResourceIdentifier>
            A dictionary with StructuralElement as key and ResourceIdentifier as value.
        javascript : str
            The Javascript code that needs to be run before taking actions on a given page.
        """
        inserted_info = {'platform_url': platform_url, 'page_type': page_type}
        page_structure_dict = {}
        for structural_element, identifier in identifiers.items():
            page_structure = {'date_format': identifier.date_format}
            if isinstance(identifier, XPath):
                page_structure['identifier_type'] = "XPath"
                page_structure['identifier'] = identifier.x_path
            elif isinstance(identifier, HTMLClass):
                page_structure['identifier_type'] = "HTMLClass"
                page_structure['identifier'] = identifier.html_classes
            elif isinstance(identifier, XPathExcept):
                page_structure['identifier_type'] = "XPathExcept"
                xpath_except_identifier = {}
                xpath_except_identifier['x_path_use'] = identifier.x_path_use.x_path
                xpath_except_identifier['x_path_remove'] = identifier.x_path_remove.x_path
                page_structure['identifier'] = xpath_except_identifier
            else:
                raise RuntimeError("Unknown type of resource identifier: " + str(type(identifier)))
            page_structure_dict[structural_element.name] = page_structure
        inserted_info['structural_elements'] = page_structure_dict

        if javascript == '':
            inserted_info['javascript'] = ''
        else:
            inserted_info['javascript'] = javascript

        if len(self.get_identifiers_from_database(platform_url, page_type)) == 0:
            self.data_api['resource identifier'].insert(inserted_info).exec()
        else:
            self.data_api['resource identifier'].update({
                'platform_url': platform_url,
                'page_type': page_type,
            }, {'$set': inserted_info}).exec()


class CustomJSONEncoder(json.JSONEncoder):
    """Implementation of JSONEncoder for converting objects into a JSON-compatible representation."""

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        if isinstance(obj, HTMLClass):
            return {'HTMLClass': obj.html_classes}
        if isinstance(obj, XPath):
            return {'XPath': obj.x_path}
        if isinstance(obj, XPathExcept):
            return {'XPathExcept': {'x_path_use': obj.x_path_use.x_path, 'x_path_remove': obj.x_path_remove.x_path}}
        return json.JSONEncoder.default(self, obj)


def user_input_json_decoder(dct):
    """Convert a dictionary of strings into a dictionary of objects.

    This function is used for converting JSON messages received from the GUI into useful objects.

    Parameters
    ----------
    dct : Dict[str, str]
        The dictionary with keys and values of type str that is converted.

    Returns
    -------
    Dict[str, any]
        The dictionary where str values are converted into objects where possible.
    """
    # Is `dct` a top-level dict, or nested inside another dict
    top_level_dict = False

    new_dct = {}
    try:
        if new_dct['javascript'] != '':
            # Return immediately the JS to execute
            new_dct['javascript'] = dct['javascript']
            return new_dct
    except KeyError:
        pass
    if 'page_type' in dct:
        new_dct['page_type'] = PageType[dct['page_type']]
        top_level_dict = True
    if 'structural_elements' in dct:
        new_dct['structural_elements'] = {}
        for name_struct_elmnt, value_dct in dct['structural_elements'].items():
            struct_elmnt = convert_name_to_structural_element(name_struct_elmnt)
            selected_html_elmnt_dcts = value_dct['selected_elements']

            if 'prev_identifier' in value_dct:
                prev_identifier_lst = value_dct['prev_identifier']
            else:
                prev_identifier_lst = {}

            # If no elements were selected and are not supposed to be present, skip this structural element
            if len(selected_html_elmnt_dcts) == 0 and len(prev_identifier_lst) == 0:
                continue

            # Otherwise convert every selected element into a HTMLElement object
            selected_html_elmnts = []
            for selected_html_elmnt_dct in selected_html_elmnt_dcts:
                html_element = HTMLElement(selected_html_elmnt_dct['outer_html'], selected_html_elmnt_dct['x_path'])
                selected_html_elmnts.append(html_element)

            # Convert ignored elements into HTMLElement objects
            ignored_html_elmnts = []
            if 'ignored_elements' in value_dct:
                ignored_html_elmnt_dcts = value_dct['ignored_elements']
                for ignored_html_elmnt_dct in ignored_html_elmnt_dcts:
                    html_element = HTMLElement(ignored_html_elmnt_dct['outer_html'], ignored_html_elmnt_dct['x_path'])
                    ignored_html_elmnts.append(html_element)

            prev_identifiers = []
            if prev_identifier_lst:
                key = next(iter(prev_identifier_lst[0]))
                if key == 'XPath':
                    prev_identifiers.append(XPath(prev_identifier_lst[0][key]))
                elif key == 'XPathExcept':
                    prev_identifiers.append(XPathExcept(XPath(prev_identifier_lst[0][key]['x_path_use']),
                                                        XPath(prev_identifier_lst[0][key]['x_path_remove'])))
                elif key == 'HTMLClass':
                    prev_identifiers.append(HTMLClass(prev_identifier_lst[0][key]))

            # Handle date format
            date_format = None
            if 'date_format' in value_dct and value_dct['date_format'] != "None":
                date_format = value_dct['date_format']

            # Store results in a tuple
            new_dct['structural_elements'][struct_elmnt] = (selected_html_elmnts, ignored_html_elmnts,
                                                            prev_identifiers, date_format)

        top_level_dict = True

    if not top_level_dict:
        new_dct = dct
    return new_dct


def convert_name_to_structural_element(name):
    """Convert a name of a structural element into its corresponding object.

    Parameters
    ----------
    name : str
        The name of a structural element.

    Returns
    -------
    StructuralElement
        The structural element object corresponding to `name`.

    Examples
    --------
    >>> convert_name_to_structural_element('LoginButton')
    <NavigationalElement.LoginButton: 4>
    """
    try:
        return NavigationalElement[name]
    except KeyError:
        try:
            return DataElement[name]
        except KeyError:
            return InputElement[name]


def _make_identifiers_json_compatible(identifiers):
    """Make dictionary of identifiers ready for conversion into JSON.

    Parameters
    ----------
    identifiers : dict<key: StructuralElement, value: ResourceIdentifier>
        A dictionary with StructuralElement as key and ResourceIdentifier as value.

    Returns
    -------
    dict<key: str, value: ResourceIdentifier>
        A dictionary where all StructuralElement keys are substituted by its string name.
    """

    new_dict = {}
    for k, v in identifiers.items():
        if v is not None:
            new_dict[k.name] = {'identifier': v, 'date_format': v.date_format}
    return new_dict
