import * as React from 'react';
import { Component } from 'react';
import { Button } from '@material-ui/core';
import WebViewer from './components/WebViewer';
import { labels } from './LabelLogic';

import '../styles/training.css';

const electron = window.require('electron');
const ipcRenderer = electron.ipcRenderer;
const remote = electron.remote;


/**
 * DoubleCheck is the class that serves as the screen after submitting the highlighted elements in the training screen.
 * 
 * In this page, the user sees a trained web page and two buttons: confirm and adjust. 
 * 
 * If the user confirms the trained web page, then THREAT/crawl has finished training this web page. 
 * If the user clicks on 'adjust', then the user is sent back to the training screen.
 * The user can then adjust the inaccurate sections of the structure and train structure again. 
 */
class DoubleCheck extends Component {

    // Constructor
    constructor(props) {
        super(props)

        this.state = {
            structure: {}
        }
    }

    webpageLoaded() {
        // Get the structure sent by the trainer from the main process
        const pathsStructure = remote.getGlobal('trained_structure');

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

        // Loop over all XPaths to get the elements satisfying that path
        for (const [label, data] of Object.entries(pathsStructure)) {
            let elements = []

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
                let ignored = this.evaluatePath(data.XPathExcept.x_path_remove, innerDoc);

                // Filter ignored elements from the selected elements
                elements = elements.filter((e) => !ignored.includes(e));
            }

            // Add elements to the structure Object under the correct label
            structure[label] = elements;
        }

        // Set the structure in the state
        this.setState({
            highlightedElements: structure
        });

        return structure
    }

    // Add styling to the gathered elements
    styleElements(structure) {
        for (const [label, elements] of Object.entries(structure)) {
            elements.forEach((element) => {
                this.styleElement(element, label);
            })
        }
    }

    // Style one specific element
    styleElement(element, label) {
        // Add border and background color to element 
        element.style.backgroundColor = labels[label].color;
        element.style.border = "thin solid rgba(0,0,0, 0.25)";

        // Don't try to improve this code, trust me
        const onClick = event => {
            event.target.style.background = labels[label].color;
            element.removeEventListener('click', onClick);
        };

        element.addEventListener('click', onClick);
        element.click();
    }

    // Confirm the trained structure is correct
    confirmStructure() {
        ipcRenderer.send("confirmation", true);
        remote.getCurrentWindow().close();
    }

    // Start training screen to adjust structure
    adjustStructure() {
        ipcRenderer.send("confirmation", false);
        remote.getCurrentWindow().close();
    }

    render() {
        return (
            <div className="DoubleCheck">
                <div className="DCWebViewer">
                    {/* Render WebViewer */}
                    <WebViewer
                        on_load={this.webpageLoaded.bind(this)}
                        page_url={'file://' + remote.getGlobal('WEBPAGE_DIRECTORY_PATH') + 'index.html'}
                    />
                </div>
                {/* Render buttons to interact */}
                <div className="DoubleCheckButtons">
                    <Button onClick={this.confirmStructure} >Confirm</Button>
                    <Button onClick={this.adjustStructure} >Adjust</Button>
                </div>
            </div>
        )
    }
}

export default DoubleCheck;
