import * as React from 'react';
import { Component, Fragment } from 'react';
import {
    Button,
    Select,
    MenuItem,
    FormControl,
    InputLabel
} from '@material-ui/core'
import WeekCalendar from 'react-week-calendar';
import PropTypes from 'prop-types';
import { v4 as uuidv4 } from 'uuid';

// import 'react-week-calendar/dist/style.css';
import "../styles/start.css";
import "../styles/schedule.css"; 

var moment = require('moment');

// Make sure some the schedule is set to start on monday
moment.updateLocale("en", {
    week: {
        dow: 1, // First day of week is Monday
    }
});

/**
 * Schedule is a class for the tab schedule. 
 * In this tab, the whole schedule can be input. 
 * 
 * A schedule is a 7-days schedule with workdays and breaks. 
 * 
 * A workday is the time in which a crawler will be crawling. 
 * A break is the time in which a crawler has a break from crawling. 
 */
class Schedule extends Component {

    // Getter for the schedule
    get schedule() {
        return this.props.schedule;
    }

    /**
     * This function is the way to update the schedule.
     * @param {Array} schedule The (updated) list of intervals
     */
    setSchedule(schedule) {
        this.props.saveConfiguration(schedule);
    }

    /**
     * Handle removing an interval from schedule 
     */
    handleEventRemove = (interval) => {
        const remainingIntervals = this.schedule.filter(element => element.id !== interval.id);

        this.setSchedule(remainingIntervals);
    }

    /**
     * Handle adjusting interval values 
     */
    handleEventUpdate = (interval) => {
        const updatedIntervals = this.schedule.map(element =>
            interval.id === element.id
                ? interval
                : element
        );

        this.setSchedule(updatedIntervals);
    }

    /**
     * Handle selecting an interval 
     */
    handleSelect = (newIntervals) => {
        newIntervals.forEach(interval => interval['id'] = uuidv4());

        this.setSchedule(this.schedule.concat(newIntervals))
    }

    render() {
        return (
            <div className="ScheduleTab">
                <div>
                    {/* Insert the schedule calendar */}
                    <WeekCalendar
                        modalComponent={Modal}
                        className={"Schedule"}
                        firstDay={moment().startOf('week')}
                        dayFormat={"dddd"}
                        scaleUnit={30}
                        selectedIntervals={this.props.schedule}
                        onIntervalSelect={this.handleSelect.bind(this)}
                        onIntervalUpdate={this.handleEventUpdate}
                        onIntervalRemove={this.handleEventRemove.bind(this)}
                    >
                    </WeekCalendar>
                </div>
            </div>
        )
    }
}

// Custom modal for the event selection
class Modal extends Component {
    constructor(props) {
        super(props);

        if (this.props.scheduleTypes.length === 0) {
            throw new Error('There are 0 schedule types to choose from. There should be at least 1 option.');
        }

        this.state = this.createInitialState();
    }

    get isCreateModal() {
        return this.props.actionType === 'create';
    }

    get isEditModal() {
        return this.props.actionType === 'edit';
    }

    createInitialState() {
        return {
            value: this.props.value || this.props.scheduleTypes[0]
        };
    }
    
    handleSave = () => {
        this.props.onSave({
            value: this.state.value
        });
    }

    handleCancel = () => {
        // Modal only closes when onRemove or onSave is called
        // so this is the simplest solution ¯\_(ツ)_/¯
        if (this.isCreateModal) {
            this.props.onRemove();
        } else {
            this.props.onSave({});
        }
    }

    handleDelete = () => {
        this.props.onRemove();
    }

    onTypeChange = event => {
        this.setState({
            value: event.target.value
        });
    }

    renderOptions =
        () => this.props.scheduleTypes.map(type => <MenuItem key={type} value={type}>{type}</MenuItem>)

    renderButtons =
        () => <div className={'flex-container justify-end'}>
                    {this.isCreateModal ? null :
                        <Button
                            onClick={this.handleDelete.bind(this)}
                            variant="outlined"
                            className={'tc-button'}
                        >Delete</Button>
                    }
                    <Button
                        onClick={this.handleCancel.bind(this)}
                        variant="outlined"
                        className={'tc-button'}
                    >Cancel</Button>
                    <Button
                        onClick={this.handleSave.bind(this)}
                        variant="outlined"
                        className={'tc-button'}
                    >Save</Button>
                </div>

    render() {
        return (
            <>
                <FormControl>
                <InputLabel htmlFor="type-selector-label">Type</InputLabel>
                <Select
                    id="type-selector"
                    labelId="type-selector-label"
                    variant="outlined"
                    value={this.state.value}
                    onChange={this.onTypeChange.bind(this)}
                >
                    {this.renderOptions()}
                </Select>
                </FormControl>
                {this.renderButtons()}
            </>
        );
    }
}

Modal.propTypes = {
    start: PropTypes.object.isRequired,
    end: PropTypes.object.isRequired,
    value: PropTypes.string,
    scheduleTypes: PropTypes.array.isRequired,
    onRemove: PropTypes.func.isRequired,
    onSave: PropTypes.func.isRequired,
    actionType: PropTypes.string
};

Modal.defaultProps = {
    scheduleTypes: ['Workday', 'Break']
};

export default Schedule