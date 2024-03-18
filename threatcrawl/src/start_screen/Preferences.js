import { FormControlLabel, FormGroup, InputAdornment, Switch, TextField, Typography } from '@material-ui/core';
import * as React from 'react';
import { Component } from 'react';

import "../styles/start.css";

/**
 * Preferences is a class for the tab preferences. 
 * In this tab, several options can be toggled. 
 * 
 * skipTraining defines if the training session should be skipped
 * sslCheck defines if it should do the SSL check or ignore it
 * defaultSchedule defines if the default schedule should be used instead of a custom schedule
 * downloadTimeout defines the timeout that is used for downloading webpages
 */
class Preferences extends Component {

    constructor(props) {
        super(props);

        this.state = {
            preferences: {
                skipTraining: false,
                sslCheck: false,
                defaultSchedule: false,
                downloadImages: true,
                downloadTimeout: 60,
                pageLoadingTimeout: 60
            }
        }

        // Bind functions to this context
        this.handleInputValues = this.handleInputValues.bind(this);
        this.togglePreference = this.togglePreference.bind(this);
        this.handleSavingConfiguration = this.handleSavingConfiguration.bind(this);
    }

    componentDidMount() {
        if (this.props.preferences) {
            this.setState({ preferences: this.props.preferences });
        }
    }

    /**
     * Handle input value changes 
     * 
     * @param {*} event is the event for the new value 
     * @param {*} element is the name of the input that has changed
     */
    handleInputValues(event, element) {
        // get new value 
        const newValue = event.target.value;

        // If the value is larger than 0, change input according to what is typed 
        if (newValue.length >= 0) {

            // Change the state of the element according to new value 
            this.setState((state) => ({
                preferences: {
                    ...state.preferences,
                    [element]: newValue
                }
            }));
        }
    }

    /**
     * Toggle preference
     * 
     * @param {*} event contains the preference that should be toggled
     */
    togglePreference(event) {
        this.setState({
            preferences: {
                ...this.state.preferences, 
                [event.target.name]: event.target.checked
            }
        })
    }

    /**
     * Saves the current preferences to TabScreen
     */
    handleSavingConfiguration() {
        this.props.saveConfiguration(this.state.preferences);
    }

    render() {
        return (
            <div className="PreferencesTab">
                <FormGroup>
                    {/* Input for download timeout */}
                    <TextField
                        id="outlined-number"
                        label="Timeout for downloads"
                        type="number"
                        placeholder={60}
                        variant="outlined"
                        size="small"
                        InputProps={{
                            endAdornment:
                                <InputAdornment position="end">
                                    in seconds
                                </InputAdornment>
                        }}
                        value={this.state.preferences.downloadTimeout}
                        onChange={(event) => {
                            this.handleInputValues(event, 'downloadTimeout');
                        }}
                        onBlur={this.handleSavingConfiguration}
                    />

                    {/* Input for page load timeout */}
                    <TextField
                        id="outlined-number"
                        label="Timeout for page loading"
                        type="number"
                        placeholder={60}
                        variant="outlined"
                        size="small"
                        InputProps={{
                            endAdornment:
                                <InputAdornment position="end">
                                    in seconds
                                </InputAdornment>
                        }}
                        value={this.state.preferences.pageLoadingTimeout}
                        onChange={(event) => {
                            this.handleInputValues(event, 'pageLoadingTimeout');
                        }}
                        onBlur={this.handleSavingConfiguration}
                    />

                    {/* Switch to toggle training */}
                    <FormControlLabel
                        control={<Switch color="primary" 
                                    name="skipTraining"
                                    checked={this.state.preferences.skipTraining} 
                                    onChange={this.togglePreference} 
                                    onBlur={this.handleSavingConfiguration}
                                />}
                        label={<Typography>Skip training session</Typography>}
                    />

                    {/* Switch to toggle image download */}
                    <FormControlLabel
                        control={<Switch color="primary" 
                                    name="downloadImages"
                                    checked={this.state.preferences.downloadImages} 
                                    onChange={this.togglePreference} 
                                    onBlur={this.handleSavingConfiguration}
                                />}
                        label={<Typography>Download images</Typography>}
                    />

                    {/* Switch to toggle SSL check */}
                    <FormControlLabel
                        control={<Switch color="primary" 
                                    name="sslCheck"
                                    checked={this.state.preferences.sslCheck} 
                                    onChange={this.togglePreference} 
                                    onBlur={this.handleSavingConfiguration}
                                />}
                        label={<Typography>SSL certificate check</Typography>}
                    />

                    {/* Switch to toggle Default schedule */}
                    <FormControlLabel
                        value="defaultSchedule"
                        control={<Switch color="primary" 
                                    name="defaultSchedule"
                                    checked={this.state.preferences.defaultSchedule} 
                                    onChange={this.togglePreference} 
                                    onBlur={this.handleSavingConfiguration}
                                />}
                        label={<Typography>Use default schedule</Typography>}
                    />
                </FormGroup>
            </div>
        );
    }
}

export default Preferences;