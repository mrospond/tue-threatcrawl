from termcolor import colored
from datetime import datetime


class Logger:

    @staticmethod
    def log(tag: str, message: str):
        tag_out = Logger.__parse_tag(tag)
        print(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ":", tag_out, message)

    @staticmethod
    def __parse_tag(tag: str):
        t = tag.lower()
        if t == "crawler":
            return colored("[CRAWLER]", "cyan")
        elif t == "database":
            return colored("[DATABASE]", "cyan")
        elif t == "type":
            return colored("[TYPE]", "yellow")
        elif t == "warning":
            return colored("[WARNING]", "yellow")
        elif t == "interpreter":
            return colored("[INTERPRETER]", "red")
        elif t == "blacklist":
            return colored("[BLACKLIST]", "red")
        elif t == "trainer":
            return colored("[TRAINER]", "magenta")
        elif t == "error":
            return colored("[ERROR]", "red")
        elif t == "schedule":
            return colored("[SCHEDULE]", "blue")
        elif t == "state":
            return colored("[STATE]", "green")
        else:
            return colored("[{}]".format(tag.upper()), "white")
