"""This file starts the crawler and CLI

After the user has pressed the Start Crawling button on the Start Screen, start_crawler.py will start this file
in a subprocess. This file then retrieves the configuration, starts the crawler thread and a CLI."""

# import json
import os

from crawler.crawler_time_controller import CrawlerTimeController
from crawler.crawler_utils import CrawlerUtils
from utils import Logger
from cli.cli import CLI
from database import create_api_from_config
from crawler.crawler_main import CrawlerMain
from config.configuration import Configuration
from config.workday import Workday
from config.crawling import Crawling
from config.link_follow_policy import LinkFollowPolicy
import threading
import sys


# Read the configuration and create an API from it
config = CrawlerUtils.read_config('config.yaml')
api = create_api_from_config(config['database'])

# Create threading events for pausing and terminating the crawler
pause = threading.Event()
terminate = threading.Event()
# This is the connection between the cli and the crawler to wake the latter up when I want to force it!
resume = threading.Condition()
solved = threading.Condition()


# Yeah, very pythonic hack to create an anonymous objects with the following fields
commands = type('', (), {'pause': pause, 'terminate': terminate, 'resume': resume, 'solved': solved})()

# Retrieve the configuration provided by the user
username = None
password = None
# Hardcode the id of the configuration that you want during testing
config_id = ''
skip_tokens = False
execute_script = ''

# Receive cli arguments
if len(sys.argv) >= 4:
    username = sys.argv[1]
    password = sys.argv[2]
    config_id = sys.argv[3]

if len(sys.argv) >= 5:
    extra_token = sys.argv[4]

    if extra_token == "skip-tokens":
        skip_tokens = True

if len(sys.argv) >= 6:
    execute_script = sys.argv[5]

user_configuration = api['configurations'].find_by_id(config_id).exec()

if user_configuration is None:
    print(f'Invalid configuration id provided: {config_id}')
    print('THREAT/crawl will quit because there is no configuration to run with')
    exit(1)

preferences_config = user_configuration['preferences']
crawling_config = user_configuration['configuration']
schedule_config = user_configuration['schedule']
keywords_config = user_configuration['keywords']

# Create a configuration, workday and crawling configuration
configuration = Configuration(Workday(), Crawling(), username, password, preferences_config, schedule_config)

# Set the values from the user input in the configuration module
if crawling_config["frontPageURL"] != "":
    configuration.crawling.platform = crawling_config["frontPageURL"]
if crawling_config["loginPageURL"] != "":
    configuration.crawling.platform_login = crawling_config["loginPageURL"]
if crawling_config["torPath"] != "":
    configuration.crawling.tor_path = crawling_config["torPath"]
if crawling_config["sectionPageURL"] != "":
    configuration.crawling.platform_section = crawling_config["sectionPageURL"]
if crawling_config["subsectionPageURL"] != "":
    configuration.crawling.platform_subsection = crawling_config["subsectionPageURL"]
if crawling_config["threadPageURL"] != "":
    configuration.crawling.platform_thread = crawling_config["threadPageURL"]
if crawling_config["readingSpeedRangeLower"] != "" and crawling_config["readingSpeedRangeUpper"] != "":
    configuration.crawling.reading_speed_range = [int(crawling_config["readingSpeedRangeLower"]),
                                                  int(crawling_config["readingSpeedRangeUpper"])]
if crawling_config["varStartTimeWorkday"] != "":
    configuration.workday.start_work_dev = int(crawling_config["varStartTimeWorkday"])
if crawling_config["varEndTimeWorkday"] != "":
    configuration.workday.end_work_dev = int(crawling_config["varEndTimeWorkday"])
if crawling_config["varStartTimeBreaks"] != "":
    configuration.workday.start_break_dev = int(crawling_config["varStartTimeBreaks"])
if crawling_config["varEndTimeBreaks"] != "":
    configuration.workday.end_break_dev = int(crawling_config["varEndTimeBreaks"])
if crawling_config["minInterruptionDuration"] != "":
    configuration.workday.min_interrupt_length = int(crawling_config["minInterruptionDuration"])
if crawling_config["maxInterruptionDuration"] != "":
    configuration.workday.max_interrupt_length = int(crawling_config["maxInterruptionDuration"])
if crawling_config["interruptionInterval"] != "":
    configuration.workday.time_btw_interrupts = int(crawling_config["interruptionInterval"])
if crawling_config["varInterruptionInterval"] != "":
    configuration.workday.time_btw_interrupts_dev = int(crawling_config["varInterruptionInterval"])
if crawling_config["timezone"]["value"] != "":
    configuration.workday.timezone = crawling_config["timezone"]["value"]
if crawling_config["linkFollowPolicy"] != "":
    if crawling_config["linkFollowPolicy"] == "all":
        configuration.crawling.link_follow_policy = LinkFollowPolicy.FOLLOW_ALL
    else:
        configuration.crawling.link_follow_policy = LinkFollowPolicy.FOLLOW_RELEVANT

configuration.crawling.relevant_keywords = keywords_config["relevantKeywords"]
configuration.crawling.blacklisted_keywords = keywords_config["blacklistedKeywords"]

configuration.setup_workday()

# Set some default values that can be added to the start screen in the future if needed
configuration.crawling.delay = (6, 12)
configuration.crawling.timeout = int(preferences_config["pageLoadingTimeout"])
configuration.crawling.download_timeout = int(preferences_config["downloadTimeout"])

# Print predefined interruption lengths for ATP
Logger.log("schedule", "Predefined interruption length: min: " + str(configuration.workday.min_interrupt_length) +
           " max: " + str(configuration.workday.max_interrupt_length))

craw_time_contr = CrawlerTimeController(configuration, username, password, config_id, execute_script)

try:
    # Create a CLI object to pass to the crawler
    cli = CLI(commands, craw_time_contr)

    # Make the CLI thread and start it
    cli_thread = threading.Thread(target=cli.execute_command, daemon=True)
    cli_thread.start()

    # Create a crawler object
    crawler = CrawlerMain(api, configuration, craw_time_contr, pause, terminate, resume, cli, solved, skip_tokens)

    # Make the crawling thread and start it
    crawly = threading.Thread(target=crawler.start_crawling)
    crawly.start()

    # wait for threads to join
    crawly.join()

    Logger.log("state", "THREAT/crawl execution terminated successfully.")
except Exception as e:
    Logger.log("error", "THREAT/crawl crashed! Look at the error below:")
    Logger.log("error", str(e))

os.system("pkill firefox.real")
sys.exit(0)
