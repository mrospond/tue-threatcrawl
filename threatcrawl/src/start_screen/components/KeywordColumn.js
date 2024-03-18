import { Button, Paper, TextField } from '@material-ui/core';
import * as React from 'react';

import '../../styles/start.css';

/**
 * KeywordColumn is a function that handles a column for keywords. 
 * 
 * In this function, a column is created for a list of keywords. 
 * This list is either for relevant or blacklisted keywords. 
 */
export default function KeywordColumn(props) {

    // Declares a new state variable
    const [currentKeyword, setCurrentKeyword] = React.useState('');

    // Handles the change when a keyword has been input  
    const handleChange = (event) => {
        setCurrentKeyword(event.target.value);
    };

    // Adds the new keyword to the list of keywords
    const addKeyword = () => {
        props.addKeyword(currentKeyword);
        setCurrentKeyword("");
    }

    return (

        // Insert column for adding keywords
        <div className="KeywordColumn">
            <Paper className="KeywordPaper">

                {/* Insert title for the keyword column */}
                <h3 className="KeywordTitle" >{props.name}</h3>

                {/* Add the keywords that have already been submitted before */}
                {props.keywordsList.map((keyword) =>
                    <p>{keyword}</p>
                )}

                {/* Input for the currently typed keyword and a button to submit the keyword */}
                <div className="KeywordInputSubmission">
                    <TextField
                        id="outlined-textarea"
                        label="Enter keyword"
                        value={currentKeyword}
                        onChange={handleChange}
                        onKeyPress={(event) => {
                            if (event.code === "Enter") {
                                addKeyword();
                            }
                        }}
                        className="KeywordInputField"
                    />
                    <Button
                        id="keyword-button"
                        onClick={addKeyword}
                        className="KeywordInputButton"
                    >
                        Add keyword
                    </Button>
                </div>
                {/* Button to clear the list of keywords */}
                <Button
                    id="clear-button"
                    onClick={props.clear}
                    className="KeywordInputButton clear"
                >
                    Clear
                </Button>
            </Paper>
        </div>
    )
}