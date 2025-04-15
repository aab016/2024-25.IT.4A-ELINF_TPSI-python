#!/usr/local/python/current/bin/python
import datetime

# https://pypi.org/project/termcolor/
from termcolor import colored, cprint

def main():
    now = datetime.datetime.now()
    print(colored("hf-trading-bot main() on {}".format(now), "magenta"))

if __name__ == '__main__':
    # Execute when the module is not initialized from an import statement.
    main()
