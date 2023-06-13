from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import bs4 as bs
from requests_html import HTMLSession
from time import sleep
import json
import re


# The Subject class Subject(subject_code, subject_name, **kwargs)
class Subject:
    def __init__(self, code, name, **kwargs):
        self.code = code  # code of the subject
        self.name = name  # name of the subject

        # Prerequisites of the subject
        self.prereq = []

        # TOoPer - The Opposite of Prerequisites (aka postrequisites, postoptional, dependancy etc) of the subject
        self.tooper = []

        # If A is a Prerequisite in B, B is a Tooper in A

        self.req_d = {}

        for name, value in kwargs.items():
            setattr(self, name, value)


def get_names_and_codes():
    # Each Faculty and its url code:
    faculties = [
        "FacultyofArts",
        "MacquarieBusinessSchool",
        "FacultyofMedicine,HealthandHumanSciences",
        "FacultyofScienceandEngineering",
    ]

    subject_l = []  # The list of Subjects

    driver = webdriver.Firefox()
    driver.set_window_size(1920, 2000)
    wait_main = WebDriverWait(driver, 10)

    for i, faculty in enumerate(faculties):
        url = f"https://coursehandbook.mq.edu.au/browse/By%20Faculty/{faculty}"
        driver.get(url)

        # close cookie popup
        if i == 0:
            element = wait_main.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, "sc-dkrFOg")))
            element.click()

        while True:
            subject_list = wait_main.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "nav[aria-labelledby='subject']")))

            wait = WebDriverWait(subject_list, 10)
            elements = wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "section1")))

            codes = [element.text for element in elements]

            elements = wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "unit-title")))

            names = [element.text for element in elements]

            assert len(codes) == len(names)

            subject_l.extend([Subject(code, name)
                             for code, name in zip(codes, names)])

            # go to next page or next faculty
            try:  # Check if there is a next page
                element = wait.until(EC.element_to_be_clickable(
                    (By.ID, "pagination-page-next")))
                element.click()
                sleep(1)
            except Exception:
                break

        print(f"Got subjects for {faculty}")
    print("Got all the subjects")
    driver.quit()
    return subject_l


def get_reqs(input_code, subject_l):
    # if the inputted code is invalid
    if input_code not in [subject.code for subject in subject_l]:
        print(f"Invalid code: {input_code}")
        return

    index = [subject.code for subject in subject_l].index(
        input_code)  # Get the index of the subject in the list

    try:  # try to find the subject site for the inputted subject
        session = HTMLSession()
        r = session.get(
            f"https://coursehandbook.mq.edu.au/2023/units/{input_code}/")
        r.html.render()

        soup = bs.BeautifulSoup(r.html.html, "lxml")
    except Exception as e:  # if it doesnt exist, return this message
        print(f"Error on: {input_code}")
        print(e)
        return

    prereq_s = soup.select_one("div.css-to4w00-Box")

    if prereq_s is None:
        subject_l[index].req_d = {}
        return

    titles = prereq_s.select("strong.css-3yvuv1-SDefaultHeading-css")
    contents = prereq_s.select("div.css-1l0t84s-Box-CardBody")

    information = {title.text: content.text for title,
                   content in zip(titles, contents)}

    subject_l[index].req_d = information

    return

    # if "Pre-requisite" in information:
    #     prereq_l = requisite_string_to_list(information["Pre-requisite"])
    #     subject_l[index].preReq = prereq_l
    #     print(prereq_l)
    #     for code in prereq_l:
    #         # for code in subject_group:
    #         if not re.fullmatch(r"^[A-Z]{4}\d{4}$", code):
    #             print(f"Invalid code: {code}")
    #             continue
    #         for subject in subject_l:
    #             if subject.code == code:
    #                 subject.tooPer.append(input_code)


# def requisite_string_to_list(s):
#     # result = re.sub(r"\sor admission to.*$", "", s)
#     # matches = re.findall(r"\((.*?)\)", result)
#     # result = [match.split(" or ") for match in matches]

#     # result = [list(filter(lambda item: not re.fullmatch(
#     #     r"^[A-Z]{4}\d{3}$", item), line)) for line in result]  # remove old subject codes

#     # return result

#     return list(re.findall(r"[A-Z]{4}\d{4}", s))


def create_subject_json(new=False):

    if new:
        subject_l = get_names_and_codes()
        subject_l_to_json(subject_l, "subjects2023_new.json")

    else:
        subject_l = json_to_subject_l("subjects2023_before.json")

    for i, subject in enumerate(subject_l, start=1):
        print(
            f"Getting requisites for {subject.code} ({str(i).zfill(len(str(len(subject_l))))}/{len(subject_l)})")
        get_reqs(subject.code, subject_l)

        if i % 20 == 0:
            subject_l_to_json(subject_l, "subjects2023_req_d.json")

        sleep(1)

    subject_l_to_json(subject_l, "subjects2023_req_d.json")

    print("DONE")


def json_to_subject_l(path):
    with open(path, "r") as f:
        subject_dict_l = json.load(f)

    subject_l = [Subject(subject_dict["code"], subject_dict["name"], req_d=subject_dict.get("req_d"))
                 for subject_dict in subject_dict_l]

    return subject_l


def subject_l_to_json(subject_l, path):
    subject_dict_l = [subject.__dict__ for subject in subject_l]

    subject_json = json.dumps(subject_dict_l, indent=4)

    with open(path, "w") as f:
        f.write(subject_json)


if __name__ == "__main__":
    create_subject_json()
