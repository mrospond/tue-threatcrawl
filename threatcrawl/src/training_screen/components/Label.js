import * as React from 'react';

import "../../styles/training.css";


/**
 * Label is a function for the default html part of all labels in the training screen. 
 */
export default function Label(props) {
    return (

        // Create a div for the label 
        <div>
            {/* If the label is selected, give the label a certain layout */}
            {/* If the label is not selected, give the label another layout */}
            {/* All labels have their own background color and text */}
            {props.selected ?
                <span className="label selected" style={{ backgroundColor: props.color }} onClick={props.onClick} >
                    {props.text}
                </span>
                :
                <span className="label" style={{ backgroundColor: props.color }} onClick={props.onClick} >
                    {props.text}
                </span>
            }
        </div>
    )
}