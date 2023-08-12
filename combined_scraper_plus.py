# -*- coding: UTF-8 -*-
"""Both web scraping projects combined for automation.
"""
import os
import codecs
import logging
import datetime as dt
import json
import codecs
import time
import random
import smtplib
import selenium
from selenium import webdriver  # , common
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
LOG_FILEPATH_JSON =   "/usr/python/combined_scraper/log/json_scraper_plus.log"
LOG_FILEPATH_DEPARR = "/usr/python/combined_scraper/log/deparr_scraper_plus.log"
LOG_FILEPATH_COMB =   "/usr/python/combined_scraper/log/combined_scraper_plus.log"
EZY_JSON_FP =         "/usr/python/combined_scraper/data/BERezy_flights_plus.json"
ALL_FLIGHTS_FP =      "/usr/python/combined_scraper/data/BERall_flights_plus.json"
FLIGHTS_DATA_FP =     "/usr/python/combined_scraper/data/flight_data_plus.csv"
TODAY = dt.datetime.strftime(dt.datetime.now(), "%Y_%m_%d")
YESTERDAY = (dt.datetime.now() - dt.timedelta(1)).strftime("%Y_%m_%d")
YESTERDAY_ = (dt.datetime.now() - dt.timedelta(2)).strftime("%Y_%m_%d")
NUM_OF_RUNS = 3  # how often per day before adding to main files
FLIGHT_CHECK = []  # note EZYs in both runs
CHROMEDRIVER_PATH = "/usr/bin/chromedriver.exe"
WINDOW_SIZE = "1920,1080"


def set_up_logger(filepath: str = "./log/log.log"):
    """Set up logger."""
    logging.basicConfig(
        level=logging.INFO,
        filename=filepath,
        filemode="a",
        format="%(asctime)s - %(levelname)8s - %(funcName)25s() - %(message)s",
    )


def wait():
    """creates a random time window to mask webdriver"""
    time.sleep(random.randint(3, 5))


def scrape_airl(airline: str = ""):
    """PROJECT-SPECIFIC.

    Opens BER website and scrapes departures for airline for TODAY
    and retuns as list of tuples (flightnum, time, desti_code)
    """
    if not airline:
        airline = "all airlines"
    logging.info("Starting scraping for departures by %s.", airline)

    dep_lst = []
    # s = Service("C:/Users/.../chromedriver.exe")
    s = Service(CHROMEDRIVER_PATH)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=s, options=chrome_options)

    logging.debug("Opening webite with ChromeDriver.")
    driver.get("https://ber.berlin-airport.de/de/" "fliegen/abfluege-ankuenfte.html")
    wait()
    wait()
    logging.debug("Waiting/checking for Cookie window.")
    cook_wind = driver.find_elements(
        "id", "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection"
    )
    wait()
    if cook_wind:
        cook_wind[0].click()
        logging.debug("Cookie window clicked.")
    wait()

    logging.debug("Scolling website to avoid error on searching objects.")
    driver.execute_script("window.scrollTo(0, 250)")
    wait()

    logging.debug("Setting time slider to 00oo hrs by clicking previous and next.")
    driver.find_element("class name", "previous").click()
    logging.debug("Previous clicked.")
    wait()
    driver.find_element("class name", "next").click()
    logging.debug("Next clicked.")
    wait()
    driver.execute_script("window.scrollTo(0, 400)")
    wait()
    type_airline = driver.find_element("class name", "flight-search__input__field")
    logging.debug("Input field selected.")
    wait()
    type_airline.clear()
    logging.debug("Input field cleared.")
    wait()
    if airline != "all airlines":
        type_airline.send_keys(airline)
        logging.info("Specific airline %s chosen.", airline)
        wait()
        type_airline.send_keys(Keys.TAB)
        logging.debug("Tab pressed.")
    wait()
    type_airline.send_keys(Keys.ENTER)
    logging.debug("Enter hit.")
    wait()

    logging.info("Loading all flights for %s on %s.", airline, TODAY)
    more_flights = True
    while more_flights:
        time.sleep(1)
        try:
            if (
                len(driver.find_elements("class name", "cmp-flightlist__action-link"))
                >= 1
            ):
                butt = driver.find_element("class name", "cmp-flightlist__action-link")
                driver.execute_script("arguments[0].click();", butt)
                time.sleep(3 + 2 * random.random())
                if driver.find_elements(
                    "class name", "cmp-flightlist__action-link.hide"
                ):
                    #     print(" done")
                    more_flights = False
                # else:
                #     print(".", end="")
        except selenium.common.exceptions.ElementNotInteractableException:
            more_flights = False
    logging.debug("All departures loaded.")

    dep_times = driver.find_elements(
        "class name", "cmp-flightlist__list__items__item--col.planned"
    )
    destinations = driver.find_elements("class name", "airport")
    flight_num = driver.find_elements("class name", "mainflight")
    if airline == "all airlines":
        al_names = driver.find_elements("class name", "info")
    for i, _ in enumerate(dep_times):
        if airline != "all airlines":
            flight = (
                flight_num[i].text[-4:],
                _.text[:-4],
                destinations[i].text.split("(")[1].split(")")[0],
                destinations[i].text.split(" (")[0],
            )
            dep_lst.append(flight)
        else:
            flight = (
                flight_num[i].text[-4:],
                _.text[:-4],
                destinations[i].text.split("(")[1].split(")")[0],
                al_names[i].text[:3],
                al_names[i].text.split("| ")[1].split(" (")[0],
                destinations[i].text.split(" (")[0],
            )
            dep_lst.append(flight)
    if airline != "all airlines":
        logging.info("%s flights found for %s.", len(dep_lst), airline)
    else:
        logging.info("%s flights found (all operators).", len(dep_times))
    wait()
    logging.debug("Closing ChromeDriver window.")
    driver.close()

    return dep_lst


def spec_airl_scrape(
    airlines: list = ["easyJet Europe", "easyJet UK", "easyJet Switzerland"],
    filepath: str = EZY_JSON_FP
):
    """All flights from the airlines for today saved to ./data/ezy.json"""

    flights_today = {}
    for airl in airlines:
        flights_today[airl] = scrape_airl(airl)
        wait()

    logging.info("Write to %s", filepath)
    flights_today_json = {TODAY: {}}
    total_flights = 0
    for airl in airlines:
        total_flights += len(flights_today[airl])
    flights_today_json[TODAY]["Total flights"] = total_flights

    for airl in airlines:
        flights_today_json[TODAY][airl] = {}
        flights_today_json[TODAY][airl]["Total flights"] = len(flights_today[airl])
        if flights_today[airl]:
            for flight in flights_today[airl]:
                flights_today_json[TODAY][airl][f"{flight[0]}"] = {}
                flights_today_json[TODAY][airl][f"{flight[0]}"]["Departure"] = flight[1]
                flights_today_json[TODAY][airl][f"{flight[0]}"]["IATA Code"] = flight[2]
                flights_today_json[TODAY][airl][f"{flight[0]}"]["Departure"] = flight[1]
                flights_today_json[TODAY][airl][f"{flight[0]}"]["Destination"] = flight[
                    -1
                ]

    # add data
    with codecs.open(filepath, "a", encoding="utf-8") as f:
        json.dump(flights_today_json, f, indent=2, ensure_ascii=False)

    # correct JSON file
    # with codecs.open(filepath, "r", encoding="utf-8") as f:
    #     incorr_json = f.read()
    # if "}{" in incorr_json:
    #     corr_json = incorr_json.replace("}{", ",")
    #     logging.info("}{ replaced")
    # elif "}\n{" in incorr_json:
    #     corr_json = incorr_json.replace("}\n{", ",")
    #     logging.info("}n{ replaced.")
    # else:
    #     logging.warning("JSON file might be incorrect")
    # with codecs.open(filepath, "w", encoding="utf-8") as f:
    #    f.write(corr_json)  # this project


def all_airlines_scrape(filepath: str = ALL_FLIGHTS_FP):
    """All flights from the airlines for today saved to ./data/ezy.json"""
    flights_today_lst = []
    flights_today_lst = scrape_airl(None)
    # get all airline codes:
    airline_names = []
    for _ in flights_today_lst:
        if _[4] not in airline_names:
            airline_names.append(_[4])
            
    logging.info("Write data of %s airlines to %s", len(airline_names), filepath)
    flights_today_json = {TODAY: {"TOTAL": 0}}

    for airl in airline_names:
        flights_today_json[TODAY][airl] = {"total": 0}
    for flight in flights_today_lst:
        flights_today_json[TODAY]["TOTAL"] += 1
        # if flight[4] in flights_today_json[TODAY].keys():
        flights_today_json[TODAY][flight[4]]["total"] += 1
        flights_today_json[TODAY][flight[4]][f"{flight[3]}{flight[0]}"] = {}
        flights_today_json[TODAY][flight[4]][f"{flight[3]}{flight[0]}"][
            "Departure"
        ] = flight[1]
        flights_today_json[TODAY][flight[4]][f"{flight[3]}{flight[0]}"][
            "IATA Code"
        ] = flight[2]
        flights_today_json[TODAY][flight[4]][f"{flight[3]}{flight[0]}"][
            "Destination"
        ] = flight[-1]
    
    # add data
    with codecs.open(filepath, "a", encoding="utf-8") as f:
        json.dump(flights_today_json, f, indent=2, ensure_ascii=False)

    # correct JSON file
    # with codecs.open(filepath, "r", encoding="utf-8") as f:
    #     incorr_json = f.read()
    # if "}{" in incorr_json:
    #     corr_json = incorr_json.replace("}{", ",")
    #     logging.info("}{ replaced")
    # elif "}\n{" in incorr_json:
    #     corr_json = incorr_json.replace("}\n{", ",")
    #     logging.info("}n{ replaced.")
    # else:
    #     logging.warning("JSON file might be incorrect")
    # with codecs.open(filepath, "w", encoding="utf-8") as f:
    #     f.write(corr_json)  # this project


def num_of_flights_from_yesterday_json_project1(this_date: str = "1981_01_24"):
    """Belongs to deparr().

    Returns num of departures from JSON scraper on the previous day.

    Args:
        this_date (str, optional): Date to be checked. Defaults to "1981_01_24".

    Returns:
        (int): number of departures on previous day in JSON scraper.
    """
    with open(ALL_FLIGHTS_FP, "r") as f:
        data = json.load(f)
    try:
        return data[this_date]["Total Flights"]
    except KeyError:
        return f"{this_date} not found in keys of BERall_flights.json"


def num_of_flights_from_yesterday_json_project(
    yesterday: str = YESTERDAY.replace("_", "-"), filepath: str = LOG_FILEPATH_COMB
):
    """checks logfile for line of yesterday's recorded departures

    Args:
        yesterday (str, optional): relevant date. Defaults to YESTERDAY.
        filepath (str, optional): relavant file. Defaults to LOG_FILEPATH_COMB.

    Returns:
        int: number of flights recorded. If None found -241 is returned
    """
    for _ in find_text(yesterday, filepath):
        if (
            " ".join(_.split(" - ")[-1].split(" ")[1:])
            == "flights found (all operators)."
        ):
            return int(_.split(" - ")[-1].split(" ")[0])
        else:
            continue
    return int(-241)


def dep_arr(filepath: str = FLIGHTS_DATA_FP):

    curr_weekday = WEEKDAYS[dt.datetime.strptime(YESTERDAY, "%Y_%m_%d").weekday()]
    with open(FLIGHTS_DATA_FP, "r", encoding="latin1") as file:
        lines = file.read().splitlines()
        last_line = lines[-1]
    last_date = last_line.split(",")[0]
    if last_date == YESTERDAY_:
        logging.info("CHECKED. %s is the last date in %s.", YESTERDAY_, FLIGHTS_DATA_FP)
    else:
        logging.warning("%s missing in %s, please check.", YESTERDAY_, FLIGHTS_DATA_FP)


    s = Service(CHROMEDRIVER_PATH)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=s, options=chrome_options)

    #   ################
    #   ## DEPARTURES ##
    #   ################

    driver.get("https://ber.berlin-airport.de/de/fliegen/abfluege-ankuenfte.html")
    wait()
    wait()
    logging.debug("Waiting/checking for Cookie window.")
    cook_wind = driver.find_elements(
        "id", "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection"
    )
    wait()
    if cook_wind:
        cook_wind[0].click()
        logging.debug("Cookie window clicked.")
    wait()

    logging.debug("Scolling website to avoid error on searching objects.")
    driver.execute_script("window.scrollTo(0, 250)")
    wait()

    logging.debug("Setting time slider to 00oo hrs by clicking previous and next.")
    driver.find_element("class name", "previous").click()
    logging.debug("Previous clicked.")
    wait()
    driver.execute_script("window.scrollTo(0, 400)")
    wait()
    type_airline = driver.find_element("class name", "flight-search__input__field")
    logging.debug("Input field selected.")
    wait()
    type_airline.clear()
    logging.debug("Input field cleared.")
    wait()
    type_airline.send_keys(Keys.ENTER)
    logging.debug("Enter hit.")
    wait()
    driver.execute_script("window.scrollTo(0, 400)")
    wait()
    logging.info("Loading all departures on %s.", YESTERDAY)
    more_flights = True
    while more_flights:
        time.sleep(1)
        try:
            if (
                len(driver.find_elements("class name", "cmp-flightlist__action-link"))
                >= 1
            ):
                butt = driver.find_element("class name", "cmp-flightlist__action-link")
                driver.execute_script("arguments[0].click();", butt)
                time.sleep(3 + 2 * random.random())
                if driver.find_elements(
                    "class name", "cmp-flightlist__action-link.hide"
                ):
                    #     print(" done")
                    more_flights = False

        except selenium.common.exceptions.ElementNotInteractableException:
            more_flights = False
    logging.info("All departures loaded.")

    # when all flights were loaded, create six lists with all relevant information
    dep_schedl_times = driver.find_elements(
        "class name", "cmp-flightlist__list__items__item--col.planned"
    )
    dep_actual_times = driver.find_elements("class name", "expected")
    destinations = driver.find_elements("class name", "airport")
    flight_nums = driver.find_elements("class name", "mainflight")
    flight_infos = driver.find_elements("class name", "info")
    flight_status = driver.find_elements("class name", "flight-status")
    logging.info("%s departures recorded for %s.", len(flight_nums), YESTERDAY)

    # create updated status list pulled data
    flight_status_corrected = []
    for _ in range(0, len(flight_status)):
        if flight_status[_].text in [
            "Gestartet",
            "Planmäßig",
            "Ende Abfertigung",
            "Ende Einstieg",
            "Abfertigung",
        ]:
            flight_status_corrected.append("departed")
        elif flight_status[_].text == "Gestrichen":
            flight_status_corrected.append("cancelled")

    # create updated list with on time / delayed information
    dep_actual_corr = []
    for _ in range(0, len(dep_actual_times)):
        if dep_actual_times[_].text == "":
            if flight_status_corrected[_] != "cancelled":
                dep_actual_corr.append("on time")
            else:
                dep_actual_corr.append(" --:-- Uhr")
        else:
            dep_actual_corr.append(dep_actual_times[_].text)

    # create list of airline operating
    airlines = []
    for _ in range(len(flight_infos)):
        airlines.append(flight_infos[_].text.split(" | ")[1])

    # create list of code shares (if applicable)
    codeshare = []
    for _ in range(len(flight_infos)):
        codes = flight_infos[_].text.replace(",", "").split(" | ")[0][3:]
        if codes[0] == " ":  # catch 3 letter airline code with 3 digit flightnum
            codes = codes.split(" ")[2:]  # remove first (=MAIN)flight number
        else:
            codes = codes.split(" ")[1:]  # remove first (=MAIN)flight number
        these_codes = ""
        if codes:
            for i in range(0, len(codes) - 1, 2):
                these_codes += f"{codes[i]}{codes[i + 1]} "
            these_codes = these_codes[:-1]
        else:
            these_codes = "---"
        codeshare.append(these_codes)
    logging.info(
        "Number of departures recorded %s in json-project: " "%s.",
        YESTERDAY,
        num_of_flights_from_yesterday_json_project(),
    )
    if (
        abs(
            int(num_of_flights_from_yesterday_json_project())
            - len(flight_nums)
        )
        > len(flight_nums) * 0.025
    ):
        logging.info(
            "Discrepancy between total numbers of both projects: " "%s (%s : %s). ",
            100
            - round(
                abs(int(num_of_flights_from_yesterday_json_project()))
                * 100
                / len(flight_nums),
                3,
            ),
            100
            - round(
                abs(int(num_of_flights_from_yesterday_json_project()))
                * 100
                / len(flight_nums),
                3,
            ),
            len(flight_nums),
        )
    logging.info("Creating %s departures as list of tuples: ", len(flight_nums))

    # DEParture: create list of FlightData objects combing all pulled data
    flights = []
    for _ in range(0, len(dep_actual_times)):
        flight = (
            YESTERDAY,
            YESTERDAY.replace("_", "") + flight_nums[_].text,
            "DEP",
            flight_nums[_].text,
            dep_schedl_times[_].text,
            flight_status_corrected[_],
            dep_actual_corr[_],
            destinations[_].text.split("(")[1].split(")")[0],
            airlines[_].split("(")[-1][:-1],
            destinations[_].text.split(" (")[0].replace(",", ""),
            airlines[_].split(" (")[0].replace(",", "."),
            codeshare[_],
            curr_weekday,
        )
        flights.append(flight)
    logging.info("Tuples appended to list, in total %s flights appended.", len(flights))
    driver.quit()
    wait()

    #   ##############
    #   ## ARRIVALS ##
    #   ##############
    wait()

    driver = webdriver.Chrome(service=s, options=chrome_options)

    driver.get("https://ber.berlin-airport.de/de/fliegen/abfluege-ankuenfte.html")
    wait()
    wait()
    logging.debug("Waiting/checking for Cookie window.")
    cook_wind = driver.find_elements(
        "id", "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection"
    )
    wait()
    if cook_wind:
        cook_wind[0].click()
        logging.debug("Cookie window clicked.")
    wait()

    logging.debug("Scolling website to avoid error on searching objects.")
    driver.execute_script("window.scrollTo(0, 250)")
    wait()

    logging.debug("Setting time slider to 00oo hrs by clicking previous and next.")
    driver.find_element("class name", "previous").click()
    logging.debug("Previous clicked.")
    wait()
    driver.find_element("class name", "icon--arrival").click()
    wait()
    driver.execute_script("window.scrollTo(0, 400)")
    wait()
    type_airline = driver.find_element("class name", "flight-search__input__field")
    logging.debug("Input field selected.")
    wait()
    type_airline.clear()
    logging.debug("Input field cleared.")
    wait()
    type_airline.send_keys(Keys.ENTER)
    logging.debug("Enter hit.")
    wait()
    driver.execute_script("window.scrollTo(0, 400)")
    wait()
    logging.info("Loading all arrivals on %s.", YESTERDAY)
    more_flights = True
    while more_flights:
        time.sleep(1)
        try:
            if (
                len(driver.find_elements("class name", "cmp-flightlist__action-link"))
                >= 1
            ):
                butt = driver.find_element("class name", "cmp-flightlist__action-link")
                driver.execute_script("arguments[0].click();", butt)
                time.sleep(3 + 2 * random.random())
                if driver.find_elements(
                    "class name", "cmp-flightlist__action-link.hide"
                ):
                    #     print(" done")
                    more_flights = False

        except selenium.common.exceptions.ElementNotInteractableException:
            more_flights = False
    logging.info("All arrivals loaded.")

    # when all flights were loaded, create six lists with all relevant information
    arr_schedl_times = driver.find_elements(
        "class name", "cmp-flightlist__list__items__item--col.planned"
    )
    arr_actual_times = driver.find_elements("class name", "expected")
    arr_destinations = driver.find_elements("class name", "airport")
    arr_flight_nums = driver.find_elements("class name", "mainflight")
    arr_flight_infos = driver.find_elements("class name", "info")
    arr_flight_status = driver.find_elements("class name", "flight-status")
    logging.info("%s arrivals recorded for %s.", len(flight_nums), YESTERDAY)

    # create updated status list of pulled data
    arr_flight_status_corrected = []
    for _ in range(0, len(arr_flight_status)):
        if arr_flight_status[_].text in [
            "Gelandet",
            "Planmäßig",
            "Ende Ausstieg",
            "Ausstieg",
        ]:
            arr_flight_status_corrected.append("arrived")
        elif arr_flight_status[_].text == "Gestrichen":
            arr_flight_status_corrected.append("cancelled")
        elif arr_flight_status[_].text == "Umgeleitet":
            arr_flight_status_corrected.append("diverted")

    # create updated list with on time / delayed information
    arr_actual_corr = []
    for _ in range(0, len(arr_actual_times)):
        if arr_actual_times[_].text == "":
            if arr_flight_status_corrected[_] not in ["cancelled", "diverted"]:
                arr_actual_corr.append("on time")
            else:
                arr_actual_corr.append(" --:-- Uhr")
        else:
            arr_actual_corr.append(arr_actual_times[_].text)

    # create list of airline operating
    arr_airlines = []
    for _ in arr_flight_infos:
        arr_airlines.append(_.text.split(" | ")[1])

    # create list of code shares (if applicable)
    arr_codeshare = []
    for _ in range(len(arr_flight_infos)):
        codes = arr_flight_infos[_].text.replace(",", "").split(" | ")[0][3:]
        if codes:
            if codes[0] == " ":  # catch 3 letter airline code with 3 digit flightnum
                codes = codes.split(" ")[2:]  # remove first (=MAIN)flight number
            else:
                codes = codes.split(" ")[1:]  # remove first (=MAIN)flight number
            these_codes = ""
            if codes:
                for i in range(0, len(codes) - 1, 2):
                    these_codes += f"{codes[i]}{codes[i + 1]} "
                these_codes = these_codes[:-1]
            else:
                these_codes = "---"

            arr_codeshare.append(these_codes)
        else:  # catches no flightnum provided
            print(
                "Incorrect data on website:",
                arr_flight_infos[_].text,
                arr_actual_times[_].text,
            )
            arr_codeshare.append(
                "ERROR,ERROR"
            )  # insert additional error two create error for csv-check
    logging.info(
        "%s arrivals, %s departures recorded before (%s)",
        len(arr_actual_times),
        len(flights),
        len(flights) - len(arr_actual_times),
    )

    # ARRivals: create list of FlightData objects combing all pulled data
    logging.info("Creating %s departures as list of tuples: ", len(arr_flight_infos))
    for _ in range(0, len(arr_actual_times)):
        flight = (
            YESTERDAY,
            YESTERDAY.replace("_", "") + arr_flight_nums[_].text,
            "ARR",
            arr_flight_nums[_].text,
            arr_schedl_times[_].text,
            arr_flight_status_corrected[_],
            arr_actual_corr[_],
            arr_destinations[_].text.split("(")[1].split(")")[0],
            arr_airlines[_].split("(")[-1][:-1],
            arr_destinations[_].text.split(" (")[0].replace(",", ""),
            arr_airlines[_].split(" (")[0].replace(",", "."),
            arr_codeshare[_],
            curr_weekday,
        )
        flights.append(flight)
    logging.info("%s tuples appended to list.", len(flights))
    driver.quit()

    logging.info("Writing %s flights to %s.", len(flights), filepath)
    for f in flights:
        with open(filepath, "a", encoding="utf-8") as file:
            file.write(f"{','.join(f)}\n")
    logging.info("Written to %s.", filepath)


def find_text(
    what: str = "1981-01-24",
    log_path: str = LOG_FILEPATH_COMB,
    beginning: bool = True,
    seperator: str = " ",
    anywhere: bool = False,
):
    """Return lines of text file as list if what inside

    Args:
        what (str, optional): what is to be found. Defaults to "1981-01-24".
        log_path (_type_, optional): which file. Defaults to "C:/users/rokar/onedrive/desktop/""combined_scraper/log/combined_scraper.log".
        beginning (bool, optional): is what the beginning of line. Defaults to True.
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


def clean_up(fi_path: str = ALL_FLIGHTS_FP):
    """Delete iteration files of fi_path"

    Args:
        fi_path (str, optional): main filename. Defaults to ALL_FLIGHTS_FP.
    """
    for _ in generate_filenames(fi_path):
        os.remove(_)
        logging.info("%s deleted.", _)
    logging.info("Cleaning of %s complete.", fi_path)


def add_data_json(main_file: str = "", new_data_fp: str = ""):
    """Append JSON data to main file.

    Args:
        main_file (str, optional): duh. Defaults to "".
        new_data_fp (str, optional): double duh. Defaults to "".

    Returns:
        bool: True if date of new_data_fp is in main_file.keys()
    """
    # load both main and new file
    logging.info("Appending data from %s to %s.", new_data_fp, main_file)

    # test change utf-8 to cp1252
    with codecs.open(main_file, "r", encoding="latin1") as fi:
        main_dict = json.load(fi)
    with codecs.open(new_data_fp, "r", encoding="latin1") as fi:
        new_dict = json.load(fi)
    new_date = list(new_dict.keys())
    # append new data and save
    main_dict.update(new_dict)
    new_ = json.dumps(main_dict, ensure_ascii=False)
    with open(main_file, "w", encoding="latin1") as f:
        f.write(new_)
    # with codecs.open(main_file, "w", encoding="latin1") as fi:
    #     json.dump(main_dict, fi, indent=2)
    # check new date is in keys of main file:
    with codecs.open(main_file, "r", encoding="latin1") as fi:
        complete_dict = json.load(fi)

    if new_date[0] in list(complete_dict.keys()):
        logging.info("Data from %s appended to %s", str(new_date[0]), main_file)
        return True
    logging.warning(
        "Appending data from %s to %s NOT SUCCESFUL.", new_data_fp, main_file
    )
    return False


def add_data_csv(main_file: str = "", new_data_fp: str = ""):
    """Append CSV data to main file.

    Args:
        main_file (str, optional): duh. Defaults to "".
        new_data_fp (str, optional): double duh. Defaults to "".

    Returns:
        bool: True if date of new_data_fp is in main_file.keys()
    """
    # load both main and new file
    logging.info("Appending data from %s to %s.", new_data_fp, main_file)
    with open(new_data_fp, "r", encoding="latin1") as fi:
        new_data = fi.read().splitlines()
    new_date = new_data[-1].split(",")[0]

    # append new data and save
    with open(main_file, "a", encoding="latin1") as fi:
        for _ in new_data:
            fi.write(f"{_}\n")

    # check new date is date of last line in main_file:
    with open(main_file, "r", encoding="latin1") as fi:
        complete_data = fi.read().splitlines()
    if new_date == complete_data[-1].split(",")[0]:
        logging.info("Data from %s appended to %s", str(new_date[0]), main_file)
        return True
    logging.warning(
        "Appending data from %s to %s NOT SUCCESFUL.", new_data_fp, main_file
    )
    return False


def generate_filenames(fi_path: str = FLIGHTS_DATA_FP):
    """Returns the filenames according to NUM_OF_RUNS."""
    filename = "".join(fi_path.split(".")[:-1]) + "_" + TODAY
    if fi_path[:2] == "./":
        filename = "." + filename
    file_end = fi_path.split(".")[-1]
    return [f"{filename}-0{_}.{file_end}" for _ in range(1, NUM_OF_RUNS + 1)]


def files_identical(fi_lst: list):
    contents = []
    for fi in fi_lst:
        with open(fi, "r", encoding="utf-8") as file:
            contents.append(file.read())
    identicals = []
    for i in range(NUM_OF_RUNS):
        identicals.append(contents[0] == contents[i])
    if all(identicals):
        return True
    return False


def check_iter(
    ezys_fp: str = EZY_JSON_FP,
    all_als_fp: str = ALL_FLIGHTS_FP,
    fli_dat_fp: str = FLIGHTS_DATA_FP,
):
    """Check and return current iteration of runs.

    Args:
        ezys_fp (str, optional): filepath to EZY-JSON. Defaults to EZY_JSON_FP.
        all_als_fp (str, optional): filepath to ALL AIRLINES-JSON. Defaults to ALL_FLIGHTS_FP.
        fli_dat_fp (str, optional): filepath to FLIGHT_DATA-CSV. Defaults to FLIGHTS_DATA_FP.

    Returns:
        _type_: list of filenames for this run's filename.
    """
    last_iters = []
    for fi in [ezys_fp, all_als_fp, fli_dat_fp]:
        for it in range(1, NUM_OF_RUNS + 1):
            filename = "".join(fi.split(".")[:-1]) + "_" + TODAY
            if fi[:2] == "./":
                filename = "." + filename
            file_end = fi.split(".")[-1]
            this_file = filename + f"-0{it}." + file_end
            if not os.path.exists(this_file):
                last_iters.append((this_file))
            else:
                continue
            break
    if len(set([_.split(".")[-2][-2:] for _ in last_iters])) != 1:
        logging.warning("Mismatching iterations of files.")
    return last_iters


def main():
    """Run main function"""
    set_up_logger(LOG_FILEPATH_COMB)
    logging.info("######################## %s #######################", TODAY)
#    main_files = [FLIGHTS_DATA_FP]
    main_files = [EZY_JSON_FP, ALL_FLIGHTS_FP, FLIGHTS_DATA_FP]
    airlines = ["easyJet Europe", "easyJet UK", "easyJet Switzerland"]
    for main_file in main_files:
        file_lst = generate_filenames(fi_path=main_file)
        if not os.path.exists(file_lst[-1]):
            for fi in file_lst:
                if not os.path.exists(fi):
                    logging.info("Getting data for %s.", fi.split("/")[-1])
                    if main_file.split("/")[-1][:7] == "BERall_":
                        all_airlines_scrape(filepath=fi)
                    elif main_file.split("/")[-1][:7] == "flight_":
                        dep_arr(filepath=fi)
                    else:
                        spec_airl_scrape(airlines=airlines, filepath=fi)
                    break
            logging.info("# # # %s complete  # # #", fi.split("/")[-1])
        else:
            logging.info(
                "All %s runs of %s complete, checking contents.", NUM_OF_RUNS, main_file
            )
            if files_identical(fi_lst=file_lst):
                logging.info(
                    "All %s iterations identical, adding to %s.", NUM_OF_RUNS, main_file
                )
                if file_lst[-1].split(".")[-1] == "json":
                    if add_data_json(main_file=main_file, new_data_fp=file_lst[-1]):
                        logging.info("Deleting iterations of %s", main_file)
                        clean_up(fi_path=main_file)
                elif file_lst[-1].split(".")[-1] == "csv":
                    if add_data_csv(main_file=main_file, new_data_fp=file_lst[-1]):
                        logging.info("Deleting iterations of %s", main_file)
                        clean_up(fi_path=main_file)
                send_mail()

            logging.info("# # # # # # # #  All scrapers complete  # # # # # # # #")

if __name__ == "__main__":
    # main()

    add_data_csv("./data/flight_data_plus.csv", "./data/flight_data_plus_2023_08_12-03.csv")
    clean_up("./data/flight_data_plus.csv")
    # all_airlines_scrape()
