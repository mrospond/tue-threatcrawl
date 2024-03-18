import * as React from 'react';
import { Tabs, Tab, Snackbar } from '@material-ui/core';
import InputConfiguration from './InputConfiguration';
import Keywords from './Keywords';
import Schedule from './Schedule';
import Confirmation from './components/Confirmation';
import { Component } from 'react';
import Alert from '@material-ui/lab/Alert';
import moment from 'moment';
import aesjs from 'aes-js';
import { v4 as uuidv4 } from 'uuid';
import { defaultValues, defaultSchedule } from './DefaultValues';

import "../styles/start.css";
import Preferences from './Preferences';

// Set a key for the encryption of usernames and passwords (created from random numbers, should probably be stored somewhere else)
const key = [22, 23, 12, 4, 1, 28, 15, 23, 19, 15, 19, 19, 2, 6, 7, 18, 31, 9, 3, 31, 28, 27, 19, 1, 25, 19, 26, 11, 8, 18, 5, 24];

const electron = window.require('electron');
const ipcRenderer = electron.ipcRenderer;
const remote = electron.remote;

/**
 * TabScreen is the class with the main functionality for the start screen. 
 * 
 * In this screen, the user has the possibility to visit three tabs. 
 * These tabs can that together form the full input configuration for a session. 
 * 
 * The tabs are: 
 * configuration: for multiple (random) necessary input values 
 * keywords: for input of relevant and blacklisted keywords 
 * schedule: for the input of the schedule with workdays and breaks 
 */
class TabScreen extends Component {

    constructor(props) {
        super(props)

        this.state = {
            popupOpen: false,
            selectedTab: 0,
            preferences: {
                skipTraining: false,
                sslCheck: false,
                defaultSchedule: false,
                downloadImages: true,
                downloadTimeout: 60,
                pageLoadingTimeout: 60
            },
            configuration: {},
            keywords: {
                relevantKeywords: [],
                blacklistedKeywords: []
            },
            schedule: [],
            unchanged: false
        }

        // Bind functions to this context
        this.saveConfiguration = this.saveConfiguration.bind(this);
        this.keepConfiguration = this.keepConfiguration.bind(this);
        this.sendConfiguration = this.sendConfiguration.bind(this);
    }

    componentWillMount() {
        // Check if a configuration is set
        const selectedConfig = remote.getGlobal('selectedConfiguration');

        // If there is a config, save it in the state
        if (selectedConfig) {
            // Decrypt username and password
            const usernameHex = selectedConfig.configuration.username;
            const passwordHex = selectedConfig.configuration.password;

            // Generate decryption object
            var aesCtr = new aesjs.ModeOfOperation.ctr(key, new aesjs.Counter(4));

            // Decrypt
            var username = this.decrypt(usernameHex, aesCtr);
            var password = this.decrypt(passwordHex, aesCtr);

            // Overwrite the config values
            const configuration = { ...selectedConfig.configuration, username, password }

            // Put the schedule in the correct structure
            var schedule = this.adjustSchedule(selectedConfig);

            // Update the state
            this.setState({
                preferences: selectedConfig.preferences,
                configuration: configuration,
                keywords: selectedConfig.keywords,
                schedule: schedule,
                unchanged: true
            });
        }
    }

    adjustSchedule(selectedConfig) {
        // Adjust schedule config to work with the schedule tab
        let schedule = [];
        let dayCount = 0

        // For each day, add the workdays and breaks
        for (const intervals of Object.values(selectedConfig.schedule)) {
            // Add workdays
            for (let i = 0; i < intervals.workday.length; i += 2) {
                // Get the start and end moments
                let day = moment().startOf('week').add(dayCount, 'days');
                let starttime = intervals.workday[i].split(':');
                let endtime = intervals.workday[i + 1].split(':');
                let start = moment(day)
                    .hour(starttime[0])
                    .minute(starttime[1])
                    .second(0);
                let end = moment(day)
                    .hour(endtime[0])
                    .minute(endtime[1])
                    .second(0);
                // Push it to the list
                schedule.push({ start, end, value: "Workday", id: uuidv4() })
            }
            // Add breaks
            for (let i = 0; i < intervals.breaks.length; i += 2) {
                // Get start and end moments
                let day = moment().startOf('week').add(dayCount, 'days');
                let starttime = intervals.breaks[i].split(':');
                let endtime = intervals.breaks[i + 1].split(':');
                let start = moment(day)
                    .hour(starttime[0])
                    .minute(starttime[1])
                    .second(0);
                let end = moment(day)
                    .hour(endtime[0])
                    .minute(endtime[1])
                    .second(0);
                // Push it to the list
                schedule.push({ start, end, value: "Break", id: uuidv4() });
            }
            // Remember amount of days added
            dayCount += 1;
        }

        return schedule
    }

    encrypt(text, aesCtr) {
        // Encrypt the credentials with AES
        var textBytes = aesjs.utils.utf8.toBytes(text);
        var textEncrypted = aesCtr.encrypt(textBytes);
        var textHex = aesjs.utils.hex.fromBytes(textEncrypted);

        return textHex
    }

    decrypt(textHex, aesCtr) {
        // Decrypt the credentials with AES
        var textEncrypted = aesjs.utils.hex.toBytes(textHex);
        var textDecrypted = aesCtr.decrypt(textEncrypted);
        var text = aesjs.utils.utf8.fromBytes(textDecrypted);

        return text
    }

    /**
     * handle changing from one tab to another and changing the selected tab. 
     */
    handleTabChange = (event, newValue) => {
        this.setState({
            selectedTab: newValue
        });
    }

    /**
     * Handle closing the popup 
     */
    handlePopupClose = (event, reason) => {
        // If the user clicked away don't close the popup
        if (reason === 'clickaway') {
            return;
        }

        // Otherwise do close the popup 
        this.setState({
            popupOpen: false
        });
    };

    /**
     * save the configuration to the state 
     */
    saveConfiguration(tab, data) {
        this.setState({
            [tab]: data,
            unchanged: false
        });
    }

    // Keep selected configuration and start crawler
    keepConfiguration() {
        // Get the selected config and needed values
        const config = remote.getGlobal('selectedConfiguration');
        const configuration_id = Buffer.from(config._id.id).toString('hex');;
        const username = this.state.configuration.username;
        const password = this.state.configuration.password;
        
        // Start the crawler and close the window
        ipcRenderer.send('start-crawler', { configuration_id, username, password });
        remote.getCurrentWindow().close();
    }

    // Send configuration
    sendConfiguration() {
        // Check if mandatory fields have been filled in
        if (!this.state.configuration.torPath
            || !this.state.configuration.frontPageURL
            || !this.state.configuration.sectionPageURL
            || !this.state.configuration.threadPageURL
            || !this.state.configuration.loginPageURL) {
            // Create a popup to notify the user
            this.setState({
                popupOpen: true
            })
            return
        }
        
        // Preferences is gotten from this.state.preferences
        let preferences = this.state.preferences

        // Check if either a schedule has been filled in or the default schedule should be used
        if (!this.state.preferences.defaultSchedule) {
            if (this.state.schedule.length === 0) {
                // Ask the user if default schedule is preferred
                const clicked = remote.dialog.showMessageBoxSync(remote.getCurrentWindow(), {
                    message: "No schedule is created, do you want to use the default schedule?",
                    type: "question",
                    buttons: ["Yes", "No"],
                    defaultId: 0,
                    cancelId: 1
                });    
                // Set the boolean accordingly
                if (clicked === 0) {
                    this.setState({
                        preferences: { ...this.state.preferences, defaultSchedule: true }
                    });    
                    preferences.defaultSchedule = true
                } else {
                    return
                }    
            }    
        }    

        // Configuration is gotten from this.state.configuration
        // To allow default values, the values are retrieved separately
        let configuration = {
            "frontPageURL": this.state.configuration.frontPageURL,
            "sectionPageURL": this.state.configuration.sectionPageURL,
            "subsectionPageURL": this.state.configuration.subsectionPageURL || "",
            "threadPageURL": this.state.configuration.threadPageURL,
            "loginPageURL": this.state.configuration.loginPageURL,
            "username": this.state.configuration.username || "",
            "password": this.state.configuration.password || "",
            "maxThreadAge": this.state.configuration.maxThreadAge || defaultValues.maxThreadAge,
            "maxThreadLength": this.state.configuration.maxThreadLength || defaultValues.maxThreadLength,
            "timezone": this.state.configuration.timezone || defaultValues.timezone,
            "varStartTimeWorkday": this.state.configuration.varStartTimeWorkday || defaultValues.varStartTimeWorkday,
            "varEndTimeWorkday": this.state.configuration.varEndTimeWorkday || defaultValues.varEndTimeWorkday,
            "varStartTimeBreaks": this.state.configuration.varStartTimeBreaks || defaultValues.varStartTimeBreaks,
            "varEndTimeBreaks": this.state.configuration.varEndTimeBreaks || defaultValues.varEndTimeBreaks,
            "linkFollowPolicy": this.state.configuration.linkFollowPolicy || defaultValues.linkFollowPolicy,
            "readingSpeedRangeLower": this.state.configuration.readingSpeedRangeLower || defaultValues.readingSpeedRangeLower,
            "readingSpeedRangeUpper": this.state.configuration.readingSpeedRangeUpper || defaultValues.readingSpeedRangeUpper,
            "maxInterruptionDuration": this.state.configuration.maxInterruptionDuration || defaultValues.maxInterruptionDuration,
            "minInterruptionDuration": this.state.configuration.minInterruptionDuration || defaultValues.minInterruptionDuration,
            "interruptionInterval": this.state.configuration.interruptionInterval || defaultValues.interruptionInterval,
            "varInterruptionInterval": this.state.configuration.varInterruptionInterval || defaultValues.varInterruptionInterval,
            "torPath": this.state.configuration.torPath,
        }

        // this.state.keywords is always up-to-date (by design), so it can be used directly
        let keywords = this.state.keywords;

        // The schedule should be parsed to send the needed data
        // First add the weekdays for translating from int to weekday
        const weekdays = {
            1: "monday",
            2: "tuesday",
            3: "wednesday",
            4: "thursday",
            5: "friday",
            6: "saturday",
            0: "sunday"
        }

        // Create schedule object
        let schedule = {
            monday: { workday: [], breaks: [] },
            tuesday: { workday: [], breaks: [] },
            wednesday: { workday: [], breaks: [] },
            thursday: { workday: [], breaks: [] },
            friday: { workday: [], breaks: [] },
            saturday: { workday: [], breaks: [] },
            sunday: { workday: [], breaks: [] },
        }

        // Take default schedule if no schedule is created
        if (this.state.preferences.defaultSchedule) {
            schedule = defaultSchedule;
        } else {
            // Add all events planned
            this.state.schedule.forEach((event) => {

                // Get the start and end moments of the event
                let start = event.start._d;
                let end = event.end._d;

                // Get the day of the event
                let day = weekdays[start.getDay()];

                // Retrieve the time from the moment objects
                let startTime = start.getHours() + ":" + start.getMinutes();
                let endTime = end.getHours() + ":" + end.getMinutes();

                // Filter type of event
                if (event.value === "Workday") {
                    schedule[day].workday = [startTime, endTime];
                } else if (event.value === "Break") {
                    schedule[day].breaks = schedule[day].breaks.concat([startTime, endTime]);
                } else {
                    console.error("Invalid event: " + event);
                }
            })
        }

        let data = { preferences, configuration, keywords, schedule };

        // The username and password are sensitive data, so they must not be stored in plaintext
        const username = data.configuration.username;
        const password = data.configuration.password;

        // Encrypt the credentials with AES
        var aesCtr = new aesjs.ModeOfOperation.ctr(key, new aesjs.Counter(4));

        const usernameHex = this.encrypt(username, aesCtr)
        const passwordHex = this.encrypt(password, aesCtr)

        data.configuration.username = usernameHex;
        data.configuration.password = passwordHex;

        // Send the configuration to be saved by the database
        ipcRenderer.send('save-configuration', data);
        ipcRenderer.on('save-configuration', (event, configuration_id) => {
            // Start the crawler and close the window
            ipcRenderer.send('start-crawler', { configuration_id, username, password });
            remote.getCurrentWindow().close();
        });
    }

    render() {
        // Select the correct tab to show
        let tab = null
        switch(this.state.selectedTab){
            case 0: 
                tab = 
                    <Preferences
                        preferences={this.state.preferences}
                        saveConfiguration={(data) => {
                            this.saveConfiguration("preferences", data)
                        }}
                    />
                break;
            case 1:
                tab =             
                    <InputConfiguration
                        configuration={this.state.configuration}
                        saveConfiguration={(data) => {
                            this.saveConfiguration("configuration", data)
                        }}
                    />
                break;
            case 2:
                tab = 
                    <Keywords
                        keywords={this.state.keywords}
                        saveConfiguration={(data) => {
                            this.saveConfiguration("keywords", data)
                        }}
                    />
                break;
            case 3:
                tab = 
                    <Schedule
                        schedule={this.state.schedule}
                        saveConfiguration={(data) => {
                            this.saveConfiguration("schedule", data)
                        }}
                    />
                break;
            default: 
                break;
        }

        return (
            // Show the tab screen 
            <div className="Tabs">
                <div className="TabScreen">
                    {/* Show the available tabs and make the selected tab another color */}
                    <Tabs
                        value={this.state.selectedTab}
                        onChange={this.handleTabChange}
                        indicatorColor="primary"
                        textColor="primary"
                        centered
                    >
                        <Tab className="Tab" label="Preferences" />
                        <Tab className="Tab" label="Configuration" />
                        <Tab className="Tab" label="Keywords" />
                        <Tab className="Tab" label="Schedule" />
                    </Tabs>
                </div>

                {/* Add the content of the tab according to the one selected */}
                <div className="TabContent">
                    {tab}
                </div>

                {/* Add buttons for all tabs */}
                <Confirmation sendConfiguration={this.state.unchanged ? this.keepConfiguration : this.sendConfiguration} />

                {/* Add a popup to notify user about filling in required fields */}
                <div>
                    <Snackbar open={this.state.popupOpen}
                        autoHideDuration={6000}
                        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
                        onClose={this.handlePopupClose}
                    >
                        <Alert onClose={this.handlePopupClose} severity="error">
                            Please enter all required fields!
                        </Alert>
                    </Snackbar>
                </div>
            </div>
        )
    }
}

export default TabScreen;