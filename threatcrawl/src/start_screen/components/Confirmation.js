import * as React from 'react';
import { Button } from '@material-ui/core';

import "../../styles/start.css";
import BackButton from '../../components/BackButton';

/**
 * Confirmation is a function that returns buttons in the start screen tabs. 
 */
export default function Confirmation(props) {

    return (
        <div className="ConfirmationButtons">

            {/* Add the button to go back */}
            <BackButton />

            {/* Add the button 'start crawler' to go to training screen and confirm platform structure */}
            <Button
                className="rightAlignedButton"
                onClick={props.sendConfiguration}
            >
                Start crawler
            </Button>
        </div>
    );
}
