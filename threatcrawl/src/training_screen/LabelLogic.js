import * as React from 'react';

import "../styles/training.css";
import Label from './components/Label';

/**
 * LabelLogic is a file that handles the logic behind the labels on the training screen 
 */

/**
 * The constant labels consists of all possible labels with type and styling
 */
export const labels = {
    HomeButton: {
        type: "nav",
        text: "Home",
        color: "#d500ffbb"
    },
    NextPageButton: {
        type: "nav",
        text: "Next button",
        color: "#00fffbbb"
    },
    PreviousPageButton: {
        type: "nav",
        text: "Previous button",
        color: "#b7ff00bb"
    },
    LoginButton: {
        type: "nav",
        text: "Log-in",
        color: "#ff006fbb"
    },
    FirstThreadPageButton: {
        type: "nav",
        text: "First thread page",
        color: "#f51720bb"
    },

    AuthorUsername: {
        type: "data",
        text: "Post author (PA)",
        color: "#ffadadcc"
    },
    AuthorNrOfPosts: {
        type: "data",
        text: "PA #posts",
        color: "#ffd6a5cc"
    },
    AuthorPopularity: {
        type: "data",
        text: "PA popularity",
        color: "#fdffb6cc"
    },
    AuthorRegistrationDate: {
        type: "data",
        text: "PA registration date",
        color: "#caffbfcc"
    },
    AuthorEmail: {
        type: "data",
        text: "PA email",
        color: "#9bf6ffcc"
    },
    PostDate: {
        type: "data",
        text: "Post date",
        color: "#b2f7efcc"
    },
    PostContent: {
        type: "data",
        text: "Post content",
        color: "#e4c1f9cc"
    },
    ThreadTitle: {
        type: "data",
        text: "Thread title",
        color: "#f2e2bacc"
    },
    ThreadSection: {
        type: "data",
        text: "Thread section",
        color: "#b7c6ffcc"
    },
    ThreadAge: {
        type: "data",
        text: "Thread age",
        color: "#e7f6ffcc"
    },
    SectionTitle: {
        type: "data",
        text: "Section title",
        color: "#edffeccc"
    },
    SubsectionTitle: {
        type: "data",
        text: "Subsection title",
        color: "#f6def6cc"
    },

    UsernameInput: {
        type: "input",
        text: "Username",
        color: "#f2c0d4dd"
    },
    PasswordInput: {
        type: "input",
        text: "Password",
        color: "#c0edf2dd"
    },
    // SearchInput: {
    //     type: "input",
    //     text: "Search",
    //     color: "#edf2c0dd"
    // },
    SubmitLoginButton: {
        type: "input",
        text: "Submit login",
        color: "#dbe9b7dd"
    },
}

/**
 * Handles selected elements by highlighting and storing them 
 */
export function addElement(context, element) {
    // Remove previous label if any
    removeElement(context, element)

    // The currently highlighted elements 
    var currHighlighted = context.state.highlightedElements;

    // The current boolean value of being unchanged
    var currUnchanged = context.state.unchanged;

    // Add border and background color to element 
    element.style.backgroundColor = labels[context.state.selectedLabel].color;
    element.style.border = "thin solid rgba(0,0,0, 0.25)";

    // If elements of this label have been selected before, add the new element
    // Else create new entry in the dictionary for the new element
    if (currHighlighted[context.state.selectedLabel]) {
        currHighlighted[context.state.selectedLabel] = currHighlighted[context.state.selectedLabel].concat(element)
    } else {
        currHighlighted[context.state.selectedLabel] = [element]
    }

    // If it wasn't changed before, toggle the currUnchanged boolean for this label
    if (currUnchanged[context.state.selectedLabel]) {
        currUnchanged[context.state.selectedLabel] = false
    }

    // Update the state with the currently highlighted elements
    context.setState((state) => ({
        highlightedElements: currHighlighted,
        unchanged: currUnchanged,
        dateFormats: { ...state.dateFormats, [state.selectedLabel]: state.dateFormatInput}
    }));
}

/**
 * Removes selected elements and removes highlighting 
 */
export function removeElement(context, element) {
    // The currently highlighted elements 
    var currHighlighted = context.state.highlightedElements;
    var currIgnored = context.state.ignoredElements;

    // The current boolean value of being unchanged
    var currUnchanged = context.state.unchanged;

    // Add border and backgroundcolor to element 
    element.style.backgroundColor = "";
    element.style.border = "";

    // If elements of this label have been selected before, remove the new element
    for (const [label, elements] of Object.entries(currHighlighted)) {
        currHighlighted[label] = elements.filter((el) => { return el !== element });
    }
    for (const [label, elements] of Object.entries(currIgnored)) {
        currIgnored[label] = elements.filter((el) => { return el !== element });
    }

    // If it wasn't changed before, toggle the currUnchanged boolean for this label
    if (currUnchanged[context.state.selectedLabel]) {
        currUnchanged[context.state.selectedLabel] = false
    }

    // Update the state with the currently highlighted elements
    context.setState({
        highlightedElements: currHighlighted,
        ignoredElements: currIgnored,
        unchanged: currUnchanged
    });
}

/**
 * Ignores selected elements and removes highlighting 
 */
 export function ignoreElement(context, element) {
    // Remove previous label if any
    removeElement(context, element)

    // Add dark border and backgroundcolor to element 
    element.style.backgroundColor = "#333333";
    element.style.border = "thin solid rgba(0,0,0, 0.25)";

    // Get the currently ignored items
    let currIgnored = context.state.ignoredElements;

    // The current boolean value of being unchanged
    var currUnchanged = context.state.unchanged;

    // If elements of this label have been selected before, add the new element
    // Else create new entry in the dictionary for the new element
    if (currIgnored[context.state.selectedLabel]) {
        currIgnored[context.state.selectedLabel] = currIgnored[context.state.selectedLabel].concat(element)
    } else {
        currIgnored[context.state.selectedLabel] = [element]
    }

    // If it wasn't changed before, toggle the currUnchanged boolean for this label
    if (currUnchanged[context.state.selectedLabel]){
        currUnchanged[context.state.selectedLabel] = false
    }
    // Update the state with the currently highlighted elements
    context.setState({
        ignoredElements: currIgnored,
        unchanged: currUnchanged
    });
}

/**
 * Handle viewer click
 * Depending on utility labels call different handlers
 */
export function handleViewerClick(context, element) {
    switch (context.state.utility) {
        case "remove": removeElement(context, element); break;
        case "ignore": ignoreElement(context, element); break;
        default: addElement(context, element);
    }
}

/**
 * Handles selecting the labels 
 */
export function selectLabel(context, label) {

    // If label is already selected, then deselect it
    // Else select the clicked label 
    if (label === context.state.selectedLabel) {
        context.setState({
            selectedLabel: ""
        });
    } else {
        context.setState({
            selectedLabel: label
        });
    }

    // Set dateformat input to the corresponding value
    console.log(context.state)
    context.setState({
        dateFormatInput: context.state.dateFormats[label] || ""
    });
}

/**
 * Handle the utility labels 
 */
export function selectUtilityLabel(context, label) {

    // If label is already selected, then deselect it
    // Else select the clicked label 
    if (label === context.state.utility) {
        context.setState({
            utility: ""
        })
    } else {
        context.setState({
            utility: label
        })
    }
}

// Labels for the front page
export const frontPageLabels = [
    "HomeButton",
    // "NextPageButton",
    // "PreviousPageButton",
    "LoginButton",
    "SectionTitle",
    "SubsectionTitle",
]

// Labels for the login page
export const loginPageLabels = [
    "HomeButton",
    // "NextPageButton",
    // "PreviousPageButton",
    // "LoginButton",
    "SectionTitle",
    "SubsectionTitle",
    "UsernameInput",
    "PasswordInput",
    "SubmitLoginButton",
]

// Labels for the section page
export const sectionPageLabels = [
    "HomeButton",
    "NextPageButton",
    "PreviousPageButton",
    // "FirstThreadPageButton",
    // "LoginButton",
    "SectionTitle",
    "SubsectionTitle",
    "ThreadTitle",
]

// Labels for the subsection page
export const subsectionPageLabels = [
    "HomeButton",
    "NextPageButton",
    "PreviousPageButton",
    // "FirstThreadPageButton",
    // "LoginButton",
    "SectionTitle",
    "SubsectionTitle",
    "ThreadTitle",
]

// Labels for the thread page
export const threadPageLabels = [
    "HomeButton",
    "NextPageButton",
    "PreviousPageButton",
    "FirstThreadPageButton",
    // "LoginButton",
    "AuthorUsername",
    "AuthorNrOfPosts",
    "AuthorPopularity",
    "AuthorRegistrationDate",
    "AuthorEmail",
    "PostDate",
    "PostContent",
    "ThreadTitle",
    "ThreadSection",
    "ThreadAge",
]

export const labelSections = (context) => {

    // Select labels according to selected page
    let labelsToShow = [];
    switch (context.state.pageType) {
        case "FrontPage": labelsToShow = frontPageLabels; break;
        case "LoginPage": labelsToShow = loginPageLabels; break;
        case "SectionPage": labelsToShow = sectionPageLabels; break;
        case "SubsectionPage": labelsToShow = subsectionPageLabels; break;
        case "ThreadPage": labelsToShow = threadPageLabels; break;
        default: labelsToShow = []; break;
    }

    // Sort them per section
    const labelsPerSection = [
        {
            text: "Navigation labels",
            labels: labelsToShow.filter((label) => {
                return labels[label].type === "nav";
            })
        },
        {
            text: "Data labels",
            labels: labelsToShow.filter((label) => {
                return labels[label].type === "data";
            })
        },
        {
            text: "Input labels",
            labels: labelsToShow.filter((label) => {
                return labels[label].type === "input";
            })
        }
    ]

    return (
        labelsPerSection.map(section =>
            <div>
                {section.labels.length > 0 ?
                    <div>
                        {/* Section title for navigation elements */}
                        <div className="SectionTitle">
                            {section.text}
                        </div>

                        {/* Labels for navigation elements */}
                        < div className="Labels" >
                            {
                                section.labels.map((label) =>
                                    <Label
                                        text={labels[label].text}
                                        color={labels[label].color}
                                        selected={label === context.state.selectedLabel}
                                        onClick={() => selectLabel(context, label)}
                                    />
                                )
                            }
                        </div>
                    </div >
                    :
                    null}
            </div>
        )
    )
}