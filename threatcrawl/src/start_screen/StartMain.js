import * as React from 'react';
import { Component } from 'react';
import { Button } from '@material-ui/core';
import { Link } from 'react-router-dom';

import "../styles/start.css";

const electron = window.require('electron');
const ipcRenderer = electron.ipcRenderer;

/**
 * StartMain is the class that serves as the first class for the start screen. 
 * 
 * In this class the user wil be able to get directed to inputting a new configuration. 
 * If the implementation of importing a file is possible (in the future), then a button can be placed here to for this. 
 */
class StartMain extends Component {

    render() {

        return (
            <div className="StartScreen" color="inherit">
                <div className="Main">

                    {/* Adds logo */}
                    <img className="Logo" src={process.env.PUBLIC_URL + '/THREATcrawl-splash.png'} alt="Logo of THREAT/crawl"/>

                    {/* Adds buttons */}
                    <div>

                        {/* Navigates to the correct screen when buttons are clicked */}
                        <Button
                            component={Link}
                            to={'/config'}
                            onClick={() => {ipcRenderer.send('resetConfig')}}
                            className="leftAlignedButton"
                        >
                            New configuration
                        </Button>

                        <Button
                            component={Link}
                            to={'/configselect'}
                            className="rightAlignedButton"
                        >
                            Select previous configuration
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

}

export default StartMain;