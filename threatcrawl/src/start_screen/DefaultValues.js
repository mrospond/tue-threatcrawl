// All default values for the configuration
export const defaultValues = {
    torPath: "/home/user/Documents/tor-browser_en-US/",
    exampleFrontPageURL: "https://www.site.com/",
    exampleSectionURL: "https://www.site.com/section",
    exampleSubsectionURL: "https://www.site.com/section/subsection",
    exampleThreadURL: "https://www.site.com/thread",
    exampleLoginURL: "https://www.site.com/login",
    username: "user123",
    password: "password123",
    maxThreadAge: Infinity,
    maxThreadLength: Infinity,
    timezone: {
        value: "Europe/Amsterdam", 
        label: "(GMT+2:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna", 
        offset: 2, 
        abbrev: "CEST", 
        altName: "Central European Summer Time"
    },
    linkFollowPolicy: "all",
    varStartTimeWorkday: 10,
    varEndTimeWorkday: 10,
    varStartTimeBreaks: 5,
    varEndTimeBreaks: 5,
    readingSpeedRangeLower: 180,
    readingSpeedRangeUpper: 240,
    maxInterruptionDuration: 15,
    minInterruptionDuration: 5,
    interruptionInterval: 90,     // time between interruptions
    varInterruptionInterval: 30 // the variance of the deviation of the interruption interval
}

// Default schedule for when it should be used
export const defaultSchedule = {
    "monday":{"workday":["8:0","18:0"],"breaks":["10:0","10:30","12:30","13:30"]},
    "tuesday":{"workday":["8:0","18:0"],"breaks":["10:0","10:30","12:30","13:30"]},
    "wednesday":{"workday":["8:0","18:0"],"breaks":["10:0","10:30","12:30","13:30"]},
    "thursday":{"workday":["8:0","18:0"],"breaks":["10:0","10:30","12:30","13:30"]},
    "friday":{"workday":["8:0","18:0"],"breaks":["10:0","10:30","12:30","13:30"]},
    "saturday":{"workday":["9:0","17:0"],"breaks":["10:0","10:30","12:30","13:30"]},
    "sunday":{"workday":["9:0","17:0"],"breaks":["10:0","10:30","12:30","13:30"]}
}