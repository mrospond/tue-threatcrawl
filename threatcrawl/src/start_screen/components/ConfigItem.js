import * as React from 'react';
import { Button } from '@material-ui/core';

import "../../styles/start.css";
import { Link } from 'react-router-dom';

/**
 * Confirmation is a function that returns buttons in the start screen tabs. 
 */
export default function ConfigItem(props) {

    // Format the timestamp gotten from the props
    let formattedTimestamp = new Intl.DateTimeFormat('en-NL',
        { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
        .format(props.timestamp)

    return (
        <div className="ConfigItem">
            {/* Show the platform URL and timestamp of the configuration */}
            <div className="configInfo">
                <table className="configInfoTable">
                    <tbody>
                        <tr>
                            <td className="configInfoTableHeader"><b>Platform:</b></td>
                            <td>{props.platform}</td>
                        </tr>
                        <tr>
                            <td className="configInfoTableHeader"><b>Time created:</b></td>
                            <td>{formattedTimestamp}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            {/* Show the buttons to select and delete a configuration */}
            <div className="configButtons">
                <Button
                    className="configButton"
                    component={Link}
                    to={'/config'}
                    onClick={props.sendConfig}
                >
                    Select
                </Button>
                <Button
                    className="configButton"
                    onClick={props.deleteConfig}
                >
                    Delete
                </Button>
            </div>
        </div>
    );
}