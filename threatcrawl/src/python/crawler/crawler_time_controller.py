"""Time controller class for the Crawler module"""
import os
import subprocess
from queue import Queue
from collections import deque
from datetime import datetime, timedelta
import random
from typing import Deque

import pytz

from config import Configuration
from utils import Logger
from crontab import CronTab


class CrawlerTimeController:
    """Time controller class for the Crawler module

    The time controller class will hold the function regarding the time and schedule of the workday.

    This class will make sure that no breaks or interrupt is skipped and will contain all information regarding time
    The class also has function to generate those interrupt and breaks that then will be scheduled.
    It is also possible to add more interrupts or add fetch delay in this class.

    Parameters
    ----------
    configurations : Configurations
        The configuration object that contains all the system and user configuration information.
    username : str
        Username to login in the target platform.
    password : str
        Password to login in the target platform.
    config_id : str
        Configuration id to fetch from the database needed for the scheduler.

    Attributes
    ----------
    __break_queue : Queue
        The queue containing the breaks for the remaining work day.
    __interrupt_queue : deque
        The dequeue containing the interrupt for the remaining work day.
    __end_crawling_time : datetime
        The end time of the crawler.
    __start_time : datetime
        The start time of the crawler.
    __username : str
        Username to login in the target platform.
    __password : str
        Password to login in the target platform.
    __config_id : str
        Configuration id to fetch from the database needed for the scheduler.
    __timezone : pytz.tzfile
        Pytz configuration of the timezone the crawler is in.
    __execute_script : str
        The full path of a bash script to execute before crawler execution. Useful to set ssh connections, etc...
    """

    def __init__(self, configurations: Configuration, username: str, password: str, config_id: str, execute_script: str):
        self.__break_queue = Queue()
        self.__interrupt_queue = deque()
        self.__end_crawling_time = None
        self.__start_time = None
        self.__username = username
        self.__password = password
        self.__config_id = config_id
        self.__configurations = configurations
        self.__execute_script = execute_script

        try:
            self.__timezone = pytz.timezone("Europe/Amsterdam")
        except (AttributeError, pytz.UnknownTimeZoneError):
            Logger.log("error", "Timezone from the configuration is unknown")
            self.__timezone = None

        if configurations is not None:
            self.__generate_schedule(configurations)

    def _add_interrupt(self, interrupt_time : int):
        """Adds an interrupt with `interrupt_time` seconds at the front of the queue with its start time the current
        time.

        Parameters
        ----------
        interrupt_time : int
            The amount of seconds the interrupt will take.

        Raises
        ----------
        BadArgumentException
            The given parameter `interrupt_time` is negative.
        """

        # if interrupt time is negative raise BadArgumentException
        if interrupt_time < 0:
            raise ValueError()

        # add a tuple (current time, interrupt_time) to the front (right) of the deque
        self.__interrupt_queue.append((self.__timezone.localize(datetime.now()), interrupt_time))

    def check_break_interrupt(self) -> int:
        """Check if at the current time of the system there is a break or interrupt scheduled.

        The function will check the queues and if there is a break then it will return the amount of time
        the crawler should pause in seconds else this function returns 0 seconds.

        Returns
        ----------
        interrupt_time : int
            The amount of seconds the crawler needs to pause.

        """

        # if break queue is not empty
        if not self.__break_queue.empty():
            # and if the first break time is passed
            if self.__break_queue.queue[0][0] <= datetime.now().astimezone(self.__timezone):
                # return the duration of that break
                return self.__break_queue.get()[1]

        # if interrupt queue contains interrupts
        if self.__interrupt_queue:
            # and if the first interrupt time is passed
            if self.__interrupt_queue[-1][0] <= datetime.now().astimezone(self.__timezone):
                # return the duration of that interrupts
                return self.__interrupt_queue.pop()[1]

        # if there are no breaks or interrupts at this time return 0
        return 0

    def get_break_schedule(self) -> Queue:
        """Returns the queue of the scheduled breaks for the workday.

        Returns
        ----------
        break_queue : Queue
            The queue for the scheduled breaks for the workday.
        """

        return self.__break_queue

    def get_interrupt_schedule(self) -> Deque:
        """Returns the queue of the scheduled interrupt for the workday.

        Returns
        ----------
        interrupt_queue : Deque
            The queue for the scheduled interrupt for the workday.
        """

        return self.__interrupt_queue

    def check_end_time(self) -> bool:
        """Returns a bool representing whether the crawler should terminate its execution.

        Returns
        -------
        bool
            Check whether the crawler should terminate its execution.
        """

        return self.__end_crawling_time <= datetime.now().astimezone(self.__timezone)

    def get_ETA(self) -> int:
        """Returns the number of seconds left of crawler activity.

        Returns
        -------
        int
            Number of seconds left of crawler activity.
        """
        return (self.__end_crawling_time - datetime.now().replace(microsecond=0).astimezone(
            self.__timezone)).total_seconds()

    def __generate_schedule(self, configurations: Configuration):
        """A private function that will generate a schedule for the workday.

        The function will make two queues, one for the interrupts and another for the breaks.
        The amount and the time of the breaks and the interrupts scheduled here depend on the configuration parameter.

        Parameters
        ----------
        configurations : Configuration
            The configuration object that contains all the system and user configuration information.
        """
        # set end time of the workday with a random deviation
        dev_end = random.randint(configurations.workday.end_work_dev * -60, configurations.workday.end_work_dev * 60)
        self.__end_crawling_time = configurations.workday.end_time + timedelta(seconds=dev_end)

        # set current time
        current_time = datetime.now().astimezone(self.__timezone)
        current_time.replace(microsecond=0)

        # set start time by adding a break starting now with a duration of start time - current time
        # with a random deviation
        dev_start = random.randint(configurations.workday.start_work_dev * -60,
                                   configurations.workday.start_work_dev * 60)
        self.__start_time = configurations.workday.start_time + timedelta(seconds=dev_start)
        start_dur = (configurations.workday.start_time - current_time + timedelta(seconds=dev_start)).total_seconds()

        # print start time with the random deviation
        Logger.log("schedule", "Start time: " + str(self.__start_time.strftime('%d/%m/%Y %H:%M:%S')) + " in " +
                   configurations.workday.timezone + " time")
        Logger.log("schedule", "End time: " + str(self.__end_crawling_time.strftime('%d/%m/%Y %H:%M:%S')) + " in " +
                   configurations.workday.timezone + " time")

        # if current time is smaller than start time add a break
        if start_dur > 0:
            self.__break_queue.put((current_time, start_dur))

        # adding the breaks to the queue
        if configurations.workday.breaks is not None:
            # for all breaks in the list
            for br in configurations.workday.breaks:
                # pick random deviation for break start and end time in seconds
                dev_break_start = random.randint(configurations.workday.start_break_dev * -60,
                                                 configurations.workday.start_break_dev * 60)
                dev_break_end = random.randint(configurations.workday.end_break_dev * -60,
                                               configurations.workday.end_break_dev * 60)

                # calculate the new start and end time and calculate the break duration in seconds
                br_start = br[0] + timedelta(seconds=dev_break_start)
                br_end = br[1] + timedelta(seconds=dev_break_end)
                br_dur = (br_end - br_start).total_seconds()

                # add break to queue in a tuple with (start time, duration)
                self.__break_queue.put((br_start, br_dur))

        # add interrupts
        # create a list from the break queue
        break_list = list(self.__break_queue.queue)

        # add end time to break list such that interrupts can be planned
        break_list.append((self.__end_crawling_time, 1))

        calculate_time = current_time.astimezone(pytz.timezone(configurations.workday.timezone))

        # for all breaks in the break queue
        for br in break_list:
            start = br[0]
            # if break is already started increase the calculate time to be after the break
            if start <= calculate_time:
                calculate_time = start + timedelta(seconds=br[1])

            # currently, no break so see if we can schedule an interrupt
            else:
                while calculate_time < br[0]:
                    # choose random time until the next interrupt in sec
                    interrupt_after = random.randint((configurations.workday.time_btw_interrupts
                                                      - configurations.workday.time_btw_interrupts_dev) * 60,
                                                     (configurations.workday.time_btw_interrupts
                                                      + configurations.workday.time_btw_interrupts_dev) * 60)

                    # set interrupt start time to be calculate time + interrupt_after
                    interrupt_start = calculate_time + timedelta(seconds=interrupt_after)

                    # choose random duration for interrupt in sec
                    interrupt_dur = random.randint(configurations.workday.min_interrupt_length * 60,
                                                   configurations.workday.max_interrupt_length * 60)

                    # if the interrupt ends and there are more than 10 min until the next break schedule this interrupt
                    # so no interrupt will be planned if it ends with less than 10 min left until the next break
                    if (br[0] - timedelta(seconds=600)) > (interrupt_start + timedelta(seconds=interrupt_dur)):
                        self.__interrupt_queue.appendleft((interrupt_start, interrupt_dur))
                        calculate_time = interrupt_start + timedelta(seconds=interrupt_dur)
                    else:
                        # no room for interrupt thus increase calculate time to be after the next break
                        calculate_time = br[0] + timedelta(seconds=br[1])

        self.__schedule_next_execution()
        if self.__start_time > self.__end_crawling_time:
            Logger.log("SCHEDULE", "The crawler won't work today. Terminating...")
            exit(0)

    def __schedule_next_execution(self):
        """Function scheduling the next execution via crontab on the system.
        """
        next_start = self.__configurations.get_start_date_next_day()
        Logger.log("schedule", "Setting next execution to " + str(next_start))
        username = subprocess.check_output('whoami').decode('utf-8').strip('\n')
        path = os.environ["PATH"]
        display = os.environ["DISPLAY"]
        script_path = '/'.join(os.path.abspath(__file__).split('/')[:-2])

        with open("/home/" + username + "/THREATcrawl-runner.sh", 'w') as f:
            f.writelines(["#!/bin/bash\n",
                          # "Xvfb :1 -screen 0 800x600x8 &\n",
                          "bash " + self.__execute_script + "\n" ## TODO this is only for DEV purposes, remove when release as this cannot be achieved via GUI. if you want it, then provide for it
                          "export PATH=\"" + path + "\"\n",
                          "export DISPLAY=\"" + display + "\" && "
                          "cd " + script_path +
                          " && /usr/bin/python3 main.py \"" +
                          self.__username + "\" \"" + self.__password + "\" " + self.__config_id + " skip-tokens " +
                          self.__execute_script + " | tee -a ~/threatcrawl.logs \n"])
        self.my_cron = CronTab(user=username)
        self.my_cron.remove_all(comment='crawler_execution')
        self.my_cron.write()
        self.job = self.my_cron.new(command='export DISPLAY=' + display + '; /usr/bin/xfce4-terminal -e '
                                            '"bash -c \'/bin/bash /home/' + username + '/THREATcrawl-runner.sh\'"',
                                    comment='crawler_execution')
        self.job.setall(next_start)
        self.my_cron.write()
