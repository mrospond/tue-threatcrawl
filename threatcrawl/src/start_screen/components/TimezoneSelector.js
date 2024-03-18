import * as React from 'react';
import TimezoneSelect from 'react-timezone-select';

import '../../styles/start.css';

/**
 * TimezoneSelector returns a dropdown with all possible timezones. 
 */
export default function TimezoneSelector(props) {

    // Handle onChange 
    const handleChange = (timezone) => {
        props.onChange(timezone);
    }

    return (
        // Adds the TimezoneSelect spinner 
        <div>
            <TimezoneSelect
                className="TimeZoneSelector"
                value={props.timezone || ""}
                onChange={handleChange}
                onBlur={props.onBlur}
            />
        </div>
    )
}