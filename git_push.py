# -*- coding: UTF-8 -*-
"""push files to github repository
"""
import subprocess
import datetime as dt
import logging

LOG_FILEPATH = "/usr/python/combined_scraper/log/git_push.log"


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
    commit_msg = f"data_backups_{dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d')}"
    logging.info("Commit message = %s", commit_msg)

    with subprocess.Popen("cd", "/usr/python/combined_scraper/databackups_auto") as change_dir:
        while not change_dir:
            continue
    logging.info("changed to git folder")

    # hardcoded
    with subprocess.Popen(["git", "add", "*_plus.*"]) as add_files:
        while not add_files.poll():
            continue
    logging.info("files added, code: %s", add_files.poll())

    # WiP
    # for file in files:
    #     add_files = subprocess.Popen(["git", "add", "*_plus.*"])
    #     while not add_files.poll():
    #         continue
    #     logging.info("%s added, code: %s", add_files.poll())

    with subprocess.Popen(["git", "commit", "-m", commit_msg, "*_test*"]) as git_commit:
        while not git_commit.poll():
            continue
        logging.info("files committed, code: %s", git_commit.poll())

    with subprocess.Popen(["git", "push"]) as git_push:
        while not git_push.poll():
            continue
    logging.info("files pushed, code: %s", git_push.poll())


def main():
    """Run main script."""
    set_up_logger(LOG_FILEPATH)
    git_push_routine()


if __name__ == "__main__":
    main()

