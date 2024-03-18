"""Class that houses the configuration"""
from typing import Tuple

from .workday import Workday
from .crawling import Crawling
from datetime import datetime, timedelta
from utils import Logger
import pytz


class Configuration:
    """Class that houses the configuration.

    This class will house all the configuration needed for the system to run smoothly. This includes the workday and
    settings related to the crawling behaviour.

    Parameters
    ---------
    workday : Workday
        The instance of the Workday class that houses the specific settings of the workday.
    crawling : Crawling
        The instance of the Crawling class that houses the specific settings related to crawling.

    Attributes
    ---------
    workday : Workday
        The instance of the Workday class that houses the specific settings of the workday.
    crawling : Crawling
        The instance of the Crawling class that houses the specific settings related to crawling.
    username : str
        The username of the platform.
    password : str
        The password of the platform.
    preferences : dict
        The selected preferences for this crawler.
    schedule : dict
        The selected week schedule for this crawler
    """

    def __init__(self, workday: Workday = None, crawling: Crawling = None, username: str = None, password: str = None,
                 preferences: dict = None, schedule: dict = None):
        self.workday = workday
        self.crawling = crawling
        self.username = username
        self.password = password
        self.preferences = preferences
        self.schedule = schedule

    def save_config(self):
        """Saves the current configuration to the database.

        Saves the current configuration, which is specified in `workday` and `crawling`, to the database. Will deal with
        connection issues that may pop up like timeout errors and such. How exactly needs to be worked out :D
        """
        raise NotImplementedError

    def __prepare_breaks_and_start_end_time(self, now: datetime, workday_date: datetime) -> Tuple[str, str, str]:
        """Obtains the theoretical start time, end time and breaks from the configuration, in relation with the day
        specified in the argument.

        Parameters
        ----------
        now : datetime
            Date representing the day for which the start time, end time and breaks neeed to be retrieved.
        workday_date: datetime
            Localized date to the relevant timezone.

        Returns
        ------
        breaks : str
            The list of breaks retrieved from the configuration
        start_time : str
            Theoretical start time for the crawler for the specified date as per configuration.
        end_time : str
            Theoretical end time for the crawler for the specified date as per configuration.
        """

        weekdaynr = now.weekday()
        # get name of the day of the week based on the numerical value of today
        # while this day is not in the schedule take the next day
        # increase workday_date by one each time we are looking at the next day in the schedule
        weekday = self.get_week_day(weekdaynr)
        while not self.schedule[weekday]["workday"]:
            weekdaynr = weekdaynr + 1
            weekday = self.get_week_day(weekdaynr)
            workday_date = workday_date + timedelta(days=1)

        # get the string value of the start and end time of the workday and split those strings on ':'
        start_time = self.schedule[weekday]["workday"][0].split(":")
        end_time = self.schedule[weekday]["workday"][1].split(":")

        # if this workday already ended look for the next day on which the crawler should work
        # and get the start and end time of that day
        """if now > (workday_date + timedelta(hours=int(end_time[0]), minutes=int(end_time[1]))):
            weekdaynr = weekdaynr + 1
            workday_date = workday_date + timedelta(days=1)
            weekday = self.get_week_day(weekdaynr)
            while not self.schedule[weekday]["workday"]:
                weekdaynr = weekdaynr + 1
                weekday = self.get_week_day(weekdaynr)
                workday_date = workday_date + timedelta(days=1)
            start_time = self.schedule[weekday]["workday"][0].split(":")
            end_time = self.schedule[weekday]["workday"][1].split(":")
        """

        breaks = self.schedule[weekday]["breaks"]
        return breaks, start_time, end_time

    def setup_workday(self):
        """Configures schedule for the next workday of the crawler

        Configures schedule for the next workday by looking at the day and time of today, and setting the breaks,
        start time and end time accordingly
        """

        # get the timezone the crawler runs in and get current time from the timezone
        # also get the numerical value of the day of the week from today and set the date
        # on which the crawlers runs on today
        timezone = pytz.timezone(self.workday.timezone)
        now = datetime.now().astimezone(timezone)
        workday_date = timezone.localize(datetime(now.year, now.month, now.day))

        breaks, start_time, end_time = self.__prepare_breaks_and_start_end_time(now, workday_date)

        # initialize i to be 0, which is used to loop through breaks and retrieve the breaks from the schedule
        i = 0

        # if the workday should have been started already, set the start time of the workday to now and look at
        # which breaks still need to happen in this workday
        if now > (workday_date + timedelta(hours=int(start_time[0]), minutes=int(start_time[1]))):
            self.workday.start_time = now

            # loop over i and if the break has been started increase i by 2 to skip over the end time of that break
            while i < len(breaks):
                break_start_time = breaks[i].split(":")
                if now < (workday_date + timedelta(hours=int(break_start_time[0]), minutes=int(break_start_time[1]))):
                    break
                i = i + 2

        # workday hasn't started yet so set start time to be the scheduled one
        else:
            self.workday.start_time = (workday_date + timedelta(hours=int(start_time[0]), minutes=int(start_time[1])))

        # set the end time of the workday to be the scheduled one
        self.workday.end_time = (workday_date + timedelta(hours=int(end_time[0]), minutes=int(end_time[1])))

        # initialize an empty break list and loop through all breaks that hasn't started yet to calculate their start
        # and end time and add those as tuples in the breaklist
        breaklist = []
        while i < len(breaks):
            break_start_time = breaks[i].split(":")
            break_end_time = breaks[i + 1].split(":")
            breaklist.append(((workday_date + timedelta(hours=int(break_start_time[0]),
                                                        minutes=int(break_start_time[1]))),
                              (workday_date + timedelta(hours=int(break_end_time[0]), minutes=int(break_end_time[1])))))
            i = i + 2

        # set the breaks of the workday to the above created breaklist
        self.workday.breaks = breaklist

        # Print start time, breaks, and end time without the random deviation
        Logger.log("schedule", "Initial start time: " + str(self.workday.start_time.strftime("%d/%m/%Y %H:%M:%S")) +
                   " in " + timezone.zone)
        for breaktime in breaklist:
            Logger.log("schedule", "Initial breaks: " + str(breaktime[0].strftime("%d/%m/%Y %H:%M:%S")) + " --- "
                       + str(breaktime[1].strftime("%d/%m/%Y %H:%M:%S")) + " in " + timezone.zone)
        Logger.log("schedule", "Initial end time: " + str(self.workday.end_time.strftime("%d/%m/%Y %H:%M:%S")) + " in "
                   + timezone.zone)

    def get_start_date_next_day(self) -> datetime:
        """
        This function allows to obtain the date in which the scheduler should start its next execution.

        Returns
        ------
        start_time : datetime
            Actual start time for the crawler for the following day.
        """

        # get the timezone the crawler runs in and get current time from the timezone
        # also get the numerical value of the day of the week from today and set the date
        # on which the crawlers runs on today
        timezone = pytz.timezone(self.workday.timezone)
        now = datetime.now().astimezone(timezone) + timedelta(days=1)

        workday_date = timezone.localize(datetime(now.year, now.month, now.day))

        breaks, start_time, end_time = self.__prepare_breaks_and_start_end_time(now, workday_date)

        return workday_date + timedelta(hours=int(start_time[0]), minutes=int(start_time[1]))

    def get_week_day(self, weekdaynr) -> str:
        """ convert numerical day of the week value to a string with full day name

        convert numerical day of the week value to a string with full day name, and if numerical
        value is greater than 6 return corresponding day of the week by doing weekdaynr modulo 7

        Returns
        -------
        str
            string with name of the day of the week
        """

        # make sure  0 <= weekdaynr <= 6 and that this nr is corresponding to the correct day of the week
        weekdaynr = weekdaynr % 7

        # return the correct day of the week based on the weekdaynr
        if weekdaynr == 0:
            return "monday"
        elif weekdaynr == 1:
            return "tuesday"
        elif weekdaynr == 2:
            return "wednesday"
        elif weekdaynr == 3:
            return "thursday"
        elif weekdaynr == 4:
            return "friday"
        elif weekdaynr == 5:
            return "saturday"
        if weekdaynr == 6:
            return "sunday"
