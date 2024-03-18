"""Class that houses the configuration for the workday"""


class Workday:
    """Class that houses the configuration for the workday

    Class that houses the configuration for the workday. This includes the start time of the workday, the end time of
    the workday, the variance of the random deviations on those times, the breaks and the variance of the random
    deviations on the break times.

    Attributes
    ---------
    start_time : datetime
        The start time of the workday.
    end_time : datetime
        The end time of the workday.
    start_work_dev : int
        The variance of the random deviation of `start_time`.
    end_work_dev : int
        The variance of the random deviation of `end_time`.
    start_break_dev : int
        The variance of the random deviation of the break start time.
    end_break_dev : int
        The variance of the random deviation of the break end time.
    breaks : list of tuples<datetime, datetime>
        List of tuples, where each tuple represents a break. The first element of the tuple is the break start time and
        the second element of the tuple is the break end time.
    timezone : str
        String representation of the timezone that this workday applies to.
    min_interrupt_length : int
        Int with the minimum duration of an interrupt in minutes
    max_interrupt_length : int
        Int with the maximum duration of an interrupt in minutes
    time_btw_interrupts : int
        Int with the average amount of minutes between interrupts
    time_btw_interrupts_dev : int
        The variance of the random deviation of the time between interrupts.
    """

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_work_dev = None
        self.end_work_dev = None
        self.start_break_dev = None
        self.end_break_dev = None
        self.breaks = None
        self.timezone = None
        self.min_interrupt_length = None
        self.max_interrupt_length = None
        self.time_btw_interrupts = None
        self.time_btw_interrupts_dev = None
