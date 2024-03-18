import * as React from 'react';

import "../styles/start.css"
import Button from '@material-ui/core/Button';
import { useHistory } from 'react-router-dom';

/**
 * BackButton returns a button to go back according to history of navigation. 
 */
export default function BackButton() {

    // The useHistory hook gives you access to the history instance that you may use to navigate
    const history = useHistory();

    return (
        // Return the button to go back
        <Button
            className="rightAlignedButton"
            onClick={() => { history.go(-1) }}
        >
            Go back
        </Button>
    )
}
