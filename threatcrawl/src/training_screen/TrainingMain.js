import * as React from 'react';
import { Component } from 'react';
import { Button, FormControl, InputAdornment, InputLabel, MenuItem, Select, Snackbar, TextField, Tooltip, IconButton } from '@material-ui/core';
import ToggleButton from '@material-ui/lab/ToggleButton';
import ToggleButtonGroup from '@material-ui/lab/ToggleButtonGroup';
import "../styles/training.css";
import WebViewer from './components/WebViewer';
import { labels, handleViewerClick, labelSections } from './LabelLogic';
import Alert from '@material-ui/lab/Alert';
import { FaRegQuestionCircle } from 'react-icons/fa';

const electron = window.require('electron');
const ipcRenderer = electron.ipcRenderer;
const remote = electron.remote;

// The possible utility options
const utilityOptions = ["add", "remove", "ignore"]

/**
 * TrainingMain is the main class for the training screen. 
 * 
 * In this screen, the user sees a web page that the user should highlight with the provided labels. 
 * Once the user is done with highlighting, they can train this web page and will be sent to the doucle check screen.
 */
class TrainingMain extends Component {

    // Constructor
    constructor(props) {
        super(props);

        // Set initial state
        this.state = this.constructInitialState();
    }

    constructInitialState() {
        return {
            highlightedElements: {},
            ignoredElements: {},
            dateFormats: {},
            unchanged: {},
            selectedLabel: "",
            utility: utilityOptions[0],
            pageType: "",
            dateFormatInput: "",
            pageTypePopupOpen: false,
            page_url: this.props.page_url,
            viewer_key: 0,
            javascript: ""
        };
    }

    componentDidMount() {
        // Retrieve structure
        this.retrieveStructure();

        // Set page type if known
        const pageType = remote.getGlobal("pageType")
        if (pageType) {
            this.setState({
                pageType: pageType
            });
        }
    }

    retrieveStructure() {
        // Retrieve identifiers from structure gotten from database
        let identifiers = {};
        let allDateFormats = {};
        for (const [pageType, {structure, date_formats}] of Object.entries(remote.getGlobal('identifiers'))) {
            identifiers[pageType] = structure;
            allDateFormats[pageType] = date_formats;
        }

        this.setState({
            identifiers: identifiers,
            allDateFormats: allDateFormats
        })
    }

    webpageLoaded() {
        // Get the structure sent by the trainer from the main process
        const pathsStructure = remote.getGlobal('trained_structure');

        // If there was a structure saved, then select the elements and highlight them
        // Else use the identifiers for the selected pagetype from the database
        if (pathsStructure) {
            // Split date formats and identifiers
            let elemIdentifiers = {}
            let dateFormats = {}
            for (const [label, {identifier, date_format}] of Object.entries(pathsStructure)) {
                elemIdentifiers[label] = identifier
                dateFormats[label] = date_format
            }
            // Retrieve and highlight the correct elements
            let structure = this.getElementsFromPath(elemIdentifiers);
            this.styleElements(structure);
            // Save the identifiers
            this.setState({
                dateFormats: dateFormats
            })
        } else if (this.state.pageType) {
            // Retrieve and highlight the correct elements
            let structure = this.getElementsFromPath(this.state.identifiers[this.state.pageType]);
            this.styleElements(structure);
        }

    }

    // Gets all elements from an xPath
    evaluatePath(path, innerDoc) {
        // Find all elements
        let xPathResult = innerDoc.evaluate(
            path,
            innerDoc,
            null,
            XPathResult.ANY_TYPE,
            null
        );

        // Push each found element to the array
        let elements = [];
        let thisElement = xPathResult.iterateNext();
        while (thisElement) {
            elements.push(thisElement)
            thisElement = xPathResult.iterateNext();
        }

        // Return the found elements
        return elements
    }

    // Uses the XPaths to get the DOM elements
    getElementsFromPath(pathsStructure) {
        const viewer = document.getElementById('viewer');
        const innerDoc = viewer.contentDocument;

        // Object to save the gathered elements
        let structure = {};
        let ignoredElements = {};
        let unchanged = {};

        // Loop over all XPaths to get the elements satisfying that path
        for (const [label, data] of Object.entries(pathsStructure)) {
            let elements = []
            let ignored = []

            // Change way of getting the elements depending on the method used
            if (data.HTMLClass) {
                data.HTMLClass.forEach((className) => {
                    // Get all elements with a certain class
                    const classResult = innerDoc.getElementsByClassName(className);

                    elements.push(...classResult);
                })
            } else if (data.XPath) {
                // Evaluate the given xPath
                elements = this.evaluatePath(data.XPath, innerDoc);
            } else if (data.XPathExcept) {
                // Evaluate the given xPath for selected elements
                elements = this.evaluatePath(data.XPathExcept.x_path_use, innerDoc);

                // Evaluate the given xPath for ignored elements
                ignored = this.evaluatePath(data.XPathExcept.x_path_remove, innerDoc);

                // Filter ignored elements from the selected elements
                elements = elements.filter((e) => !ignored.includes(e));
            }

            // Add elements to the structure Object under the correct label
            structure[label] = elements;

            // If ignored, add them to ignored elements
            if (ignored) {
                ignoredElements[label] = ignored
            }

            unchanged[label] = true
        }

        // Set the structure in the state
        this.setState({
            highlightedElements: structure,
            ignoredElements: ignoredElements,
            unchanged: unchanged
        });

        return structure
    }

    // Add styling to the gathered elements
    styleElements(structure) {
        // Highlight the given structure
        for (const [label, elements] of Object.entries(structure)) {
            elements.forEach((element) => {
                this.styleElement(element, label);
            });
        }
    }

    styleElement(element, label) {
        // Add border and background color to element 
        element.style.backgroundColor = labels[label].color;
        element.style.border = "thin solid rgba(0,0,0, 0.25)";
    }

    /**
     * Handles the highlighted elements and saves in a dictionary. 
     * 
     * The dictionary saves for each label the XPath of all elements that are highlighted with that color. 
     */
    trainStructure() {

        // Check if page type is selected
        if (!this.state.pageType) {
            // Open popup
            this.setState({
                pageTypePopupOpen: true
            });

            // Don't send structure
            return
        }

        // Array for saving the labels with XPath of highlighted elements
        let structural_elements = {};

        // Loop through the highlighted elements 
        for (const label of Object.keys(labels)) {

            // For each label, create labelXPath that saves the XPaths for highlighted elements 
            let labelElements = {
                selected_elements: [],
                ignored_elements: [],
                date_format: "",
                prev_identifier: []
            };

            // For each highlighted element, push the XPath and outerHTML
            if (this.state.highlightedElements[label]) {
                this.state.highlightedElements[label].forEach(element => {
                    labelElements.selected_elements.push({
                        x_path: this.getXPath(element),
                        outer_html: element.outerHTML
                    });
                });
            }

            // For each ignored element, push the XPath and outerHTML 
            if (this.state.ignoredElements[label]) {
                this.state.ignoredElements[label].forEach(element => {
                    labelElements.ignored_elements.push({
                        x_path: this.getXPath(element),
                        outer_html: element.outerHTML
                    });
                });
            }

            // For the current label, save the date format
            labelElements.date_format = this.state.dateFormats[label];

            // For each label, push the XPaths array with label name in dictionary 
            structural_elements[label] = labelElements;
        }

        // Add the elements that are not on this webpage
        if (this.state.identifiers[this.state.pageType]) {
            for (let [label, elements] of Object.entries(this.state.identifiers[this.state.pageType])) {
                if (!(structural_elements[label].selected_elements.length > 0) || this.state.unchanged[label]) {
                    structural_elements[label].prev_identifier.push(elements)
                }
            }
        }

        // Set data to send
        const data = {
            page_type: this.state.pageType,
            structural_elements,
            javascript: document.getElementById("txtjs").value
        };


        // Send structure to main process
        ipcRenderer.send('structure', data);

        // Close the training screen
        remote.getCurrentWindow().close();
    }

    /**
     * Gets the xPath of the given element
     */
    getXPath(elm) {
        let i, sib;

        // Loop over the path and save the steps
        for (var segs = []; elm && elm.nodeType === 1; elm = elm.parentNode) {
            for (i = 1, sib = elm.previousSibling; sib; sib = sib.previousSibling) {
                if (sib.localName === elm.localName) i++;
            };
            segs.unshift(elm.localName.toLowerCase() + '[' + i + ']');
        };

        // Return the path through the segment
        return segs.length ? '/' + segs.join('/') : null;
    }

    reloadViewer(pageType) {
        // Refresh the WebViewer
        this.setState({
            ...this.constructInitialState(),
            // Save pageType if given
            pageType: pageType,
            // Set correct date formats
            dateFormats: this.state.allDateFormats[pageType] || {},
            // Changing the key will reload the WebViewer, discarding all changes in the webpage
            viewer_key: Math.floor(Math.random() * 1e9),
        });

        // Get back the structure from the database
        this.retrieveStructure();
    }

    /**
     * Resets the highlighted elements and structure. 
     */
    resetStructure() {
        // Send reset signal to main process
        ipcRenderer.send('reset', this.state.pageType);
        
        // Reload the viewer to erase highlighting
        this.reloadViewer(this.state.pageType);
    }


    /**
     * Handles selecting page type from the spinner
     */
    handlePageType(event) {
        // Save selected page type
        let pageType = event.target.value

        // Save page type in state
        this.setState({
            pageType: pageType,
        })

        // Reload viewer
        this.reloadViewer(pageType);
    }

    /**
     * Handle closing the popup
     */
    handlePopupClose = (event, reason) => {
        // If the user clicked away don't close the popup
        if (reason === 'clickaway') {
            return;
        }

        // Otherwise do close the popup
        this.setState({
            pageTypePopupOpen: false
        });
    };

    /**
     * Handles saving the dateformat input
     */
    handleDateInput(event) {
        // Save dateformat 
        let dateFormat = event.target.value
        this.setState({
            dateFormatInput: dateFormat,
            dateFormats: { ...this.state.dateFormats, [this.state.selectedLabel]: dateFormat }
        })
    }

    /**
     * Handles selecting the utility
     */
    handleSelectedUtility(event, utility) {
        if (utility !== null) {
            this.setState({
                utility: utility
            })
        }
    }

    executeJS() {
        // Unfortunately the page is not really active by design, so I cannot execute there the Javascript to verify.
        // Function('"use strict";return (' + document.getElementById("txtjs").value + ')')();
        // eval(document.getElementById("txtjs").value)
        // document.evaluate('//*[@id="top"]/div[2]/div[2]/div[2]/div/nav/div/div[3]/div[1]/a[2]/span', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()
        // document.getElementById("buttonExecuteJS").disabled = true;

        // Set data to send
        const data = {
            javascript: document.getElementById("txtjs").value
        };

        // Send communication about JavaScript execution to main process
        ipcRenderer.send('structure', data);

        // Close the training screen
        remote.getCurrentWindow().close();
    }

    prefillClick() {
        document.getElementById("txtjs").value = "document.evaluate('YOUR_XPATH_HERE', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()"    
    }

    render() {

        // Text to be shown in the date format tooltip
        const tooltipText = <div>
            The syntax that is expected from 'date_format' is listed
            <a href="https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior" target="_blank" rel="noreferrer"> here </a>.
        </div>
  
        return (      
            <div className="TrainingScreen">
                <div>
                    {/* Render the WebViewer */}
                    <div className="TSWebViewer">
                        <WebViewer
                            label={this.state.selectedLabel}
                            handleClick={(element) => { handleViewerClick(this, element) }}
                            showAlert={true}
                            on_load={this.webpageLoaded.bind(this)}
                            page_url={'file://' + remote.getGlobal('WEBPAGE_DIRECTORY_PATH') + 'index.html'}
                            key={this.state.viewer_key}
                        />
                    </div>

                    {/* Render the sidebar with labels and buttons */}
                    <div className="TrainingSidebar">

                        {/*Perform operations before training*/}
                        <div>
                        <label for="txtjs">JavaScript to execute:</label>
                        <textarea id="txtjs" cols="30" rows="5"></textarea>
                        <br></br>
                        <button
                            onClick={this.prefillClick}
                            id="clickButtonJS">
                            Prefill with JS to click element
                        </button>
                        <button
                            onClick={this.executeJS}
                            id="buttonExecuteJS">
                            Execute
                        </button>
                        </div>

                        {/* Choice for page type */}
                        <FormControl
                            variant="outlined"
                            size="small"
                        >
                            <InputLabel id="demo-simple-select-outlined-label">
                                Page type
                            </InputLabel>

                            <Select
                                labelId="demo-simple-select-outlined-label"
                                id="demo-simple-select-outlined"
                                label="Page type"
                                value={this.state.pageType}
                                onChange={this.handlePageType.bind(this)}
                            >
                                <MenuItem value={"LoginPage"}>Log-in page</MenuItem>
                                <MenuItem value={"FrontPage"}>Front page</MenuItem>
                                <MenuItem value={"SectionPage"}>Section page</MenuItem>
                                <MenuItem value={"SubsectionPage"}>Subsection page</MenuItem>
                                <MenuItem value={"ThreadPage"}>Thread page</MenuItem>
                            </Select>
                        </FormControl>

                        {/* Toggle for utility options */}
                        <div className="UtilityToggle">
                            <ToggleButtonGroup
                                className="UtilityToggle"
                                exclusive
                                size="small"
                                value={this.state.utility}
                                onChange={this.handleSelectedUtility.bind(this)}
                            >
                                {utilityOptions.map(
                                    option => <ToggleButton value={option}>{option}</ToggleButton>)
                                }
                            </ToggleButtonGroup>
                        </div>

                        {/* Labels to show */}
                        {labelSections(this)}

                        {/* If a label is selected, show the date format input for that label */}
                        {this.state.selectedLabel ?
                            /* Date format input field */
                            < TextField
                                id="outlined-textarea"
                                label="Date format"
                                placeholder="DD/MM/Y"
                                InputProps={{
                                    endAdornment:
                                    <InputAdornment position="end">
                                            {/* Add tooltip */}
                                            <Tooltip title={
                                                <React.Fragment>
                                                    {tooltipText}
                                                </React.Fragment>
                                            } interactive>
                                                <IconButton style={{ backgroundColor: 'transparent' }} >
                                                    <FaRegQuestionCircle />
                                                </IconButton>
                                            </Tooltip>
                                        </InputAdornment>
                                }}
                                variant="outlined"
                                size="small"
                                value={this.state.dateFormatInput}
                                onChange={this.handleDateInput.bind(this)}
                            />
                            :
                            null
                        }

                        {/* Train button */}
                        <Button
                            className="ConfirmationStructureButton"
                            onClick={this.trainStructure.bind(this)}>
                            Train structure
                        </Button>

                        {/* Reset button */}
                        <Button
                            className="ConfirmationStructureButton"
                            onClick={this.resetStructure.bind(this)}>
                            Reset structure
                        </Button>

                    </div>

                    {/* Add a popup to notify user about selecting a page type */}
                    <div>
                        <Snackbar open={this.state.pageTypePopupOpen}
                            autoHideDuration={6000}
                            anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
                            onClose={this.handlePopupClose}
                        >
                            <Alert onClose={this.handlePopupClose} severity="error">
                                Please select a page type!
                            </Alert>
                        </Snackbar>
                    </div>
                </div>
            </div >
        );
    }
}

export default TrainingMain;