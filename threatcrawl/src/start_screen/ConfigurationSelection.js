import * as React from 'react';
import { Component } from 'react';
import ConfigItem from './components/ConfigItem';

import "../styles/start.css";

const electron = window.require('electron');
const ipcRenderer = electron.ipcRenderer;
const remote = electron.remote;

/**
 * ConfigurationSelection is the class that is used to select previously used configurations. 
 * 
 * In this class the user wil be able to select a configuration and get redirected to the configuration screen. 
 * The values of the selected configuration are filled in in the configuration screen. 
 */
class ConfigurationSelection extends Component {

    constructor(props) {
        super(props);

        this.state = {
            configurations: []
        }

        // Bind functions to this context
        this.sendConfig = this.sendConfig.bind(this)
        this.deleteConfig = this.deleteConfig.bind(this)
    }

    componentDidMount() {
        // Get configurations from database
        let configurations = remote.getGlobal("configurations") || [];
        console.log(remote.getGlobal("configurations"));
        this.setState({
            configurations: configurations.reverse()
        })
    }

    // Send selected configuration to the main process
    sendConfig(configuration) {
        ipcRenderer.send("selectConfig", configuration);
    }

    // Delete the configuration from the list and from the database
    deleteConfig(configuration) {
        // Send the configuration with the id to the main process
        ipcRenderer.send("deleteConfig", {configuration, id: configuration._id.toHexString()});
        
        // Remove it from the rendered list
        this.setState({
            configurations: this.state.configurations.filter(config => { return config !== configuration })
        })
    }

    render() {
        // Create the list of ConfigItem objects
        const configurationList = this.state.configurations.map(configuration => (
            <ConfigItem
                key={`cfi-${configuration._id}`}
                platform={configuration.configuration.frontPageURL}
                timestamp={configuration._id.getTimestamp()}
                sendConfig={() => { this.sendConfig(configuration) }}
                deleteConfig={() => { this.deleteConfig(configuration) }}
            />
        ))

        return (
            <div className="StartScreen" color="inherit">
                <div className="ConfigList">

                    {/* Render ConfigItem objects */}
                    {configurationList.length === 0 
                        ? <div>No configurations could be found in the database</div>
                        : configurationList
                    }

                </div>
            </div>
        );
    }

}

export default ConfigurationSelection;