# -*- coding: UTF-8 -*-
"""push files to github repository
"""
import os
import subprocess
import datetime as dt
import logging
import time
import smtplib

# LOG_FILEPATH = "/usr/python/combined_scraper/log/git_push.log"
LOG_FILEPATH = "/usr/python/combined_scraper/log/combined_scraper_plus.log"
TODAY = dt.datetime.strftime(dt.datetime.now(), "%Y_%m_%d")


def set_up_logger(filepath: str = "./log/log.log"):
    """Set up logger."""
    logging.basicConfig(
        level=logging.INFO,
        filename=filepath,
        filemode="a",
        format="%(asctime)s - %(levelname)8s - %(funcName)25s() - %(message)s",
    )


def git_push_routine(files: list = None):
    """PROJECT-SPECIFIC, must be run in git-folder.
    Run shell commands to push files to github repository

    Args:
        files (list, optional): _description_. Defaults to None.
    """
    commit_msg = f"data_backups_{dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d@%H:%M:%S')}"
    logging.info("Commit message = %s", commit_msg)

    wd = os.getcwd()
    os.chdir("/usr/python/combined_scraper/databackups_auto")
    logging.info("changed to git folder")

    # hardcoded
    # cp_files = subprocess.Popen(["cp", "/usr/python/combined_scraper/data/*_plus*", 
    cp_files = subprocess.Popen("cp /usr/python/combined_scraper/data/*_plus* /usr/python/combined_scraper/databackups_auto/", shell=True)
    time.sleep(2)                       
    logging.info("files copied from ../data/, code: %s", cp_files.poll())


    add_files = subprocess.Popen(["git", "add", "*_plus.*"])
    time.sleep(5)
    logging.info("files added, code: %s", add_files.poll())

    # WiP
    # for file in files:
    #     add_files = subprocess.Popen(["git", "add", "*_plus.*"])
    #     while not add_files.poll():
    #         continue
    #     logging.info("%s added, code: %s", add_files.poll())

    git_commit = subprocess.Popen(["git", "commit", "-m", commit_msg, "*_plus.*"])
    time.sleep(5)
    logging.info("files committed, code: %s", git_commit.poll())

    git_push = subprocess.Popen(["git", "push"])
    time.sleep(5)
    logging.info("files pushed, code: %s", git_push.poll())


def find_text(
    what: str = "1981-01-24",
    log_path: str = LOG_FILEPATH,
    beginning: bool = True,
    seperator: str = " ",
    anywhere: bool = False,
):
    """Return lines of text file as list if what inside

    Args:
        what (str, optional): what is to be found. Defaults to "1981-01-24".
        log_path (_type_, optional): which file. Defaults to LOG_FILEPATH.
        beginning (bool, optional): is _what_ the beginning of line. Defaults to True.
        seperator (str, optional): define seperator. Defaults to " ".
        anywhere (bool, optional): no separation of line. Defaults to False.

    Returns:
        (list, None): found lines or None
    """
    if beginning:
        anywhere = False
    with open(log_path, "r", encoding="utf-8") as file:
        raw = file.read().splitlines()
    if beginning:
        return [_ for _ in raw if _.split(seperator)[0] == what]
    if anywhere:
        return [_ for _ in raw if what in _]
    return None


def send_mail(to_address: str = "rokaruto@googlemail.com"):
    """Send email."""
    logging.info("Preparing to send email to %s", to_address)
    mail_text = f"Subject: combined_scraper.log for {TODAY}\n\n"
    logs = find_text(what=TODAY.replace("_", "-"))
    for _ in logs:
        mail_text += f"{_}\n"
    logging.info("%s lines appended to mail text.", len(logs))
    with smtplib.SMTP("smtp.mail.yahoo.com") as connection:
        connection.starttls()
        connection.login(user="ch405_15_0rd3r@yahoo.com", password="ahsdtmbcfyyekdfw")
        connection.sendmail(
            from_addr="ch405_15_0rd3r@yahoo.com",
            to_addrs=to_address,
            msg=mail_text,
        )
    logging.info("Mail sent to %s.", to_address)


def main():
    """Run main script."""
    set_up_logger(LOG_FILEPATH)
    git_push_routine()
    send_mail()

if __name__ == "__main__":
    main()

