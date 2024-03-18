import * as React from 'react';
import { Component } from 'react';
import { InputAdornment, TextField, InputLabel, FormControl, Select, Tooltip, MenuItem, IconButton } from '@material-ui/core';
import TimezoneSelector from './components/TimezoneSelector';
import { defaultValues } from './DefaultValues';
import { FaRegEye, FaRegEyeSlash, FaRegQuestionCircle } from 'react-icons/fa';


import "../styles/start.css";

/**
 * InputConfiguration is a class for the tab input configuration. 
 * In this tab, several values can be input as part of the configuration. 
 * 
 * torPath is the path on the machine to the tor browser folder
 * frontPageURL is the URL for front page of the platform that the user would like to crawl. 
 * sectionPageURL is the URL for section page of the platform that the user would like to crawl.
 * subsectionPageURL is the URL for subsection page of the platform that the user would like to crawl. (optional)
 * threadPageURL is the URL for thread page of the platform that the user would like to crawl.
 * loginPageURL is the URL for login page of the platform that the user would like to crawl. 
 * username is the value of the username that the crawler can use to log in into the platform. 
 * password is the value of the password that the crawler can use to log in into the platform. 
 * maxThreadAge is the maximum age of a thread that the crawler will use to look into the threads. NOT USED
 * maxThreadLength is the maximum length of a thread that the crawler will use to look into the threads. NOT USED
 * timezone is the value of the timezone used which the crawler crawls during the defined schedule. 
 * linkFollowPolicy is the policy to be used when encountering links on the platform.
 * varStartTimeWorkday is the variance for the start time of a workday. 
 * varEndTimeWorkday is the variance for the end time of a workday. 
 * varStartTimeBreaks is the variance for the start time of a break. 
 * varEndTimeBreaks is the variance for the end time of a break. 
 */
class InputConfiguration extends Component {

    constructor(props) {
        super(props);

        // Set the initial state
        this.state = {
            configuration: {
                frontPageURL: "",
                sectionPageURL: "",
                subsectionPageURL: "",
                threadPageURL: "",
                loginPageURL: "",
                username: "",
                password: "",
                maxThreadAge: "",
                maxThreadLength: "",
                timezone: "",
                linkFollowPolicy: "",
                varStartTimeWorkday: "",
                varEndTimeWorkday: "",
                varStartTimeBreaks: "",
                varEndTimeBreaks: "",
                torPath: "",
                readingSpeedRangeLower: "",
                readingSpeedRangeUpper: "",
                maxInterruptionDuration: "",
                minInterruptionDuration: "",
                interruptionInterval: "",
                varInterruptionInterval: ""
            },
            passwordVisible: false
        }

        // Bind functions to this context
        this.handleInputValues = this.handleInputValues.bind(this);
        this.handleSavingConfiguration = this.handleSavingConfiguration.bind(this);
        this.handleTimezone = this.handleTimezone.bind(this);
    }

    // Set the state to the configuration selected
    componentDidMount() {
        this.setState({ configuration: this.props.configuration });
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
                configuration: {
                    ...state.configuration,
                    [element]: newValue
                }
            }));
        }
    }

    // Toggle whether the password is visible
    togglePasswordVisibility() {
        this.setState({
            passwordVisible: !this.state.passwordVisible
        })
    }

    // Handle selection of the timezone
    handleTimezone(timezone) {
        this.setState((state) => ({
            configuration: {
                ...state.configuration,
                timezone: timezone
            }
        }));
    }

    // Send current configuration to TabScreen to save
    handleSavingConfiguration() {
        this.props.saveConfiguration(this.state.configuration);
    }

    render() {

        // Define link follow policies
        const linkFollowPolicyOptions = ["all", "relevant"];

        return (
            <div className="ConfigurationTab">

                {/* Tor Browser path */}
                <TextField
                    id="outlined-textarea"
                    label="Tor Browser path *"
                    placeholder={defaultValues.torPath}
                    variant="outlined"
                    size="small"
                    value={this.state.configuration.torPath}
                    onChange={(event) => {
                        this.handleInputValues(event, 'torPath');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* URL log-in page */}
                <TextField
                    id="outlined-textarea"
                    label="URL log-in page *"
                    placeholder={defaultValues.exampleLoginURL}
                    variant="outlined"
                    size="small"
                    value={this.state.configuration.loginPageURL}
                    onChange={(event) => {
                        this.handleInputValues(event, 'loginPageURL');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* URL front page */}
                <TextField
                    id="outlined-textarea"
                    label="URL front page *"
                    placeholder={defaultValues.exampleFrontPageURL}
                    variant="outlined"
                    size="small"
                    value={this.state.configuration.frontPageURL}
                    onChange={(event) => {
                        this.handleInputValues(event, 'frontPageURL');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* URL section page */}
                <TextField
                    id="outlined-textarea"
                    label="URL section page *"
                    placeholder={defaultValues.exampleSectionURL}
                    variant="outlined"
                    size="small"
                    value={this.state.configuration.sectionPageURL}
                    onChange={(event) => {
                        this.handleInputValues(event, 'sectionPageURL');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* URL subsection page */}
                <TextField
                    id="outlined-textarea"
                    label="URL subsection page"
                    placeholder={defaultValues.exampleSubsectionURL}
                    variant="outlined"
                    size="small"
                    value={this.state.configuration.subsectionPageURL}
                    onChange={(event) => {
                        this.handleInputValues(event, 'subsectionPageURL');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />
                <p>Please note: If the target website opens the last page of a thread when clicking on a thread title, provide a link for a thread at its second or third page, allowing to learn both the first page button and the next and previous page buttons.</p>
                {/* URL thread page */}
                <TextField
                    id="outlined-textarea"
                    label="URL thread page *"
                    placeholder={defaultValues.exampleThreadURL}
                    variant="outlined"
                    size="small"
                    value={this.state.configuration.threadPageURL}
                    onChange={(event) => {
                        this.handleInputValues(event, 'threadPageURL');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Username */}
                <TextField
                    id="outlined-textarea"
                    label="Username"
                    placeholder={defaultValues.username}
                    variant="outlined"
                    size="small"
                    value={this.state.configuration.username}
                    onChange={(event) => {
                        this.handleInputValues(event, 'username');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Password */}
                <TextField
                    id="outlined-textarea"
                    label="Password"
                    type={this.state.passwordVisible ? "text" : "password"}
                    placeholder={defaultValues.password}
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end" onClick={this.togglePasswordVisibility.bind(this)}>
                                {this.state.passwordVisible ? <FaRegEyeSlash /> : <FaRegEye />}
                            </InputAdornment>
                    }}
                    variant="outlined"
                    size="small"
                    value={this.state.configuration.password}
                    onChange={(event) => {
                        this.handleInputValues(event, 'password');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Thread age */}
                {/* <TextField
                        id="outlined-number"
                        label="Maximum thread age"
                        type="number"
                        placeholder={defaultValues.maxThreadAge}
                        InputProps={{
                            endAdornment:
                                <InputAdornment position="end">
                                    in years
                                </InputAdornment>
                        }}
                        variant="outlined"
                        size="small"
                        value={this.state.configuration.maxThreadAge}
                        onChange={(event) => {
                            this.handleInputValues(event, 'maxThreadAge');
                        }}
                        onBlur={this.handleSavingConfiguration}
                    /> */}

                {/* Thread length */}
                {/* <TextField
                        id="outlined-number"
                        label="Maximum thread length"
                        type="number"
                        placeholder={defaultValues.maxThreadLength}
                        variant="outlined"
                        size="small"
                        value={this.state.configuration.maxThreadLength}
                        onChange={(event) => {
                            this.handleInputValues(event, 'maxThreadLength');
                        }}
                        onBlur={this.handleSavingConfiguration}
                    /> */}

                {/* TimeZone spinner */}
                <TimezoneSelector
                    timezone={this.state.configuration.timezone}
                    onChange={this.handleTimezone}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Link-follow-policy */}
                <FormControl
                    variant="outlined"
                    size="small"
                >
                    <InputLabel id="demo-simple-select-outlined-label">Link-follow-policy</InputLabel>
                    <Select
                        labelId="demo-simple-select-outlined-label"
                        id="demo-simple-select-outlined"
                        label="Link-follow-policy"
                        value={this.state.configuration.linkFollowPolicy}
                        onChange={(event) => {
                            this.handleInputValues(event, 'linkFollowPolicy');
                        }} 
                        onBlur={this.handleSavingConfiguration}   
                        >
                        <MenuItem value={linkFollowPolicyOptions[0]}>Follow all encountered links</MenuItem>
                        <MenuItem value={linkFollowPolicyOptions[1]}>Follow only the links with relevant keywords</MenuItem>
                    </Select>
                </FormControl>

                {/* Variance start time workday */}
                <TextField
                    id="outlined-number"
                    label="Variance start time workday"
                    type="number"
                    placeholder={defaultValues.varStartTimeWorkday}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.varStartTimeWorkday}
                    onChange={(event) => {
                        this.handleInputValues(event, 'varStartTimeWorkday');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Variance end time workday */}
                <TextField
                    id="outlined-number"
                    label="Variance end time workday"
                    type="number"
                    placeholder={defaultValues.varEndTimeWorkday}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.varEndTimeWorkday}
                    onChange={(event) => {
                        this.handleInputValues(event, 'varEndTimeWorkday');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Variance start time breaks */}
                <TextField
                    id="outlined-number"
                    label="Variance start time breaks"
                    type="number"
                    placeholder={defaultValues.varStartTimeBreaks}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.varStartTimeBreaks}
                    onChange={(event) => {
                        this.handleInputValues(event, 'varStartTimeBreaks');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Variance end time breaks */}
                <TextField
                    id="outlined-number"
                    label="Variance end time breaks"
                    type="number"
                    placeholder={defaultValues.varEndTimeBreaks}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.varEndTimeBreaks}
                    onChange={(event) => {
                        this.handleInputValues(event, 'varEndTimeBreaks');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Reading speed range lower */}
                <TextField
                    id="outlined-number"
                    label="Minimum reading speed (words per minute)"
                    type="number"
                    placeholder={defaultValues.readingSpeedRangeLower}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.readingSpeedRangeLower}
                    onChange={(event) => {
                        this.handleInputValues(event, 'readingSpeedRangeLower');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Reading speed range upper */}
                <TextField
                    id="outlined-number"
                    label="Maximum reading speed (words per minute)"
                    type="number"
                    placeholder={defaultValues.readingSpeedRangeUpper}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.readingSpeedRangeUpper}
                    onChange={(event) => {
                        this.handleInputValues(event, 'readingSpeedRangeUpper');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Minimum interrupt duration */}
                <TextField
                    id="outlined-number"
                    label="Minimum interrupt duration"
                    type="number"
                    placeholder={defaultValues.minInterruptionDuration}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.minInterruptionDuration}
                    onChange={(event) => {
                        this.handleInputValues(event, 'minInterruptionDuration');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Reading speed range upper */}
                <TextField
                    id="outlined-number"
                    label="Maximum interrupt duration"
                    type="number"
                    placeholder={defaultValues.maxInterruptionDuration}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.maxInterruptionDuration}
                    onChange={(event) => {
                        this.handleInputValues(event, 'maxInterruptionDuration');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Interrupt interval */}
                <TextField
                    id="outlined-number"
                    label="Interval between interrupts"
                    type="number"
                    placeholder={defaultValues.interruptionInterval}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.interruptionInterval}
                    onChange={(event) => {
                        this.handleInputValues(event, 'interruptionInterval');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />

                {/* Variance interrupt interval */}
                <TextField
                    id="outlined-number"
                    label="Interval between interrupts variance"
                    type="number"
                    placeholder={defaultValues.varInterruptionInterval}
                    variant="outlined"
                    size="small"
                    InputProps={{
                        endAdornment:
                            <InputAdornment position="end">
                                in minutes
                            </InputAdornment>
                    }}
                    value={this.state.configuration.varInterruptionInterval}
                    onChange={(event) => {
                        this.handleInputValues(event, 'varInterruptionInterval');
                    }}
                    onBlur={this.handleSavingConfiguration}
                />
            </div>
        );
    }
}

export default InputConfiguration;