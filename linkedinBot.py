"""
This Bot Scrapes all profiles with a particular role.
"""
import re
import time
from typing import Union, Optional

import pandas
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def extract_text_only(word: Union[list, str]) -> Optional[tuple,list]:
    """
    this function formats text.
    accepts only alpha numeric characters and some specific required special characters.
    """
    if isinstance(word, (tuple, list)):
        word = " ".join(word)
    regex = r"[^\w \.\-\+]+"
    word = re.sub(regex, "", word)
    word = word.strip()
    return word
 

def get_about(about_soup: BeautifulSoup) -> str:
    """
    this function gets the about block data of a profile.
    Args: 
        about_soup (BeautifulSoup) - This is a Soup of About Block.
    Returns: 
        a string of About Block.
    """
    about = about_soup.find("p")
    if about:
        about = about.text
        about = re.sub("\n", ".", about)
        about = extract_text_only(about)
    return about


def get_experience(experience_soup: BeautifulSoup) -> list:
    """
    this function gets all experiences of a profile.
    Args: 
        experience_soup: (BeautifulSoup) - This is a Soup of Experience Block.
     Returns:
        a list of objects, where each object represents an experience data of a profile.
    """
    total_experiences = []
    experiences = experience_soup.find_all("li", class_="experience-item")
    for exp in experiences:
        user_experience = {
            "role": None,
            "company": None,
            "company_link": None,
            "start_date": None,
            "end_date": None,
            "duration": None,
            "location": None,
            "description": None,
        }
        role = exp.find("h3", class_="profile-section-card__title").text
        user_experience["role"] = extract_text_only(role)
        job_details = exp.find("a", class_="profile-section-card__subtitle-link")
        if job_details:
            user_experience["company_link"] = job_details.get("href")
            user_experience["company"] = extract_text_only(job_details.text)
        date_details = exp.find("span", class_="date-range")
        if date_details:
            date_details = extract_text_only(date_details.text)
            date_details = list(date_details.split("-"))
            user_experience["start_date"] = date_details[0]
            user_experience["end_date"] = date_details[1]
        duration_details = exp.find("span", class_="date-range__duration")
        if duration_details:
            duration_details = extract_text_only(duration_details.text)
            user_experience["duration"] = duration_details
            user_experience["end_date"] = re.sub(
                duration_details, "", user_experience["end_date"]
            )
        user_location = exp.find("p", class_="experience-item__location")
        if user_location:
            user_location = extract_text_only(user_location.text)
            user_experience["location"] = user_location
        role_description = exp.find("p", class_="show-more-less-text__text--less")
        if role_description:
            role_description_more = exp.find(
                "p", class_="show-more-less-text__text--more"
            )
            if role_description_more:
                role_description = role_description_more
            user_experience["description"] = extract_text_only(role_description.text)

        total_experiences.append(user_experience)

    return total_experiences


def get_projects(projects_soup: BeautifulSoup) -> list:
    """
    this function gets all projects of a profile.
    Args: 
        projects_soup: (BeautifulSoup) - This is a Soup of Projects Block.
     Returns:
        a list of objects, where each object represents an project data of a profile.
    """
    total_projects = []
    projects = projects_soup.find_all("li", class_="personal-project")
    for proj in projects:
        user_project = {
            "project_name": None,
            "start_date": None,
            "end_date": None,
            "description": None,
            "project_link": None,
        }
        project_name = proj.find("h3", class_="profile-section-card__title").text
        user_project["role"] = extract_text_only(project_name)
        date_details = proj.find("span", class_="date-range")
        if date_details:
            date_details = extract_text_only(date_details.text)
            date_details = list(date_details.split("-"))
            user_project["start_date"] = date_details[0]
            if len(date_details) > 1:
                user_project["end_date"] = date_details[1]
        project_description = proj.find("p", class_="show-more-less-text__text--less")
        if project_description:
            project_description_more = proj.find(
                "p", class_="show-more-less-text__text--more"
            )
            if project_description_more:
                project_description = project_description_more
            user_project["description"] = extract_text_only(project_description.text)
        project_link = proj.find("a", class_="personal-project__button")
        if project_link:
            user_project["project_link"] = project_link.get("href")

        total_projects.append(user_project)

    return total_projects


def get_certification(certifications_soup: BeautifulSoup) -> list:
    """
    this function gets all certificates of a profile.
    Args: 
        certificates_soup: (BeautifulSoup) - This is a Soup of certificate Block.
     Returns:
        a list of objects, where each object represents an certificate data of a profile.
    """
    total_certifications = []
    certifications = certifications_soup.find_all("li", class_="profile-section-card")
    for certify in certifications:
        user_certificate = {
            "certification": None,
            "certified_by": None,
            "issued_on": None,
            "certificate_link": None,
        }
        certification = certify.find("h3", class_="profile-section-card__title")
        if certification:
            user_certificate["certification"] = extract_text_only(certification.text)
        certified_by = certify.find("h4", class_="profile-section-card__subtitle")
        if certified_by:
            user_certificate["certified_by"] = extract_text_only(certified_by.text)
        issued_on = certify.find("div", class_="certifications__date-range")
        if issued_on:
            user_certificate["issued_on"] = extract_text_only(issued_on.text)
        certificate_link = certify.find("a", class_="certifications__button")
        if certificate_link:
            user_certificate["certificate_link"] = certificate_link.get("href")

        total_certifications.append(user_certificate)

    return total_certifications


def get_basic_details(user_details: WebElement) -> dict:
    """
    this function gets all the basic data like name,current company, location, description.
    we get all this data using XPATH of the web elements.

    Args:
        user_details: (weeElement) - it is a webelement of user basic information.
    Returns:
        a dictionary, which contains basic data of the user in key,value pairs.
    """
    basic_data = {
        "user_name": None,
        "user_description": None,
        "user_location": None,
        "current_company": None,
    }
    try:
        user_name = user_details.find_element(
            By.XPATH,
            '//*[@id="main-content"]/section[1]/div/section/section[1]/div/div[2]/div[1]/h1',
        ).text
        user_name = extract_text_only(user_name)
    except Exception:
        user_name = ""

    try:
        user_description = user_details.find_element(
            By.XPATH,
            '//*[@id="main-content"]/section[1]/div/section/section[1]/div/div[2]/div[1]/h2',
        ).text
    except Exception:
        user_description = ""

    try:
        user_location = user_details.find_element(
            By.XPATH,
            '//*[@id="main-content"]/section[1]/div/section/section[1]/div/div[2]/div[1]/h3',
        ).text
        if "\n" in user_location:
            user_location = user_location.split("\n")[0]
    except Exception:
        user_location = ""

    try:
        current_company = user_details.find_element(
            By.XPATH,
            '//*[@id="main-content"]/section[1]/div/section/section[1]/div/div[2]/div[2]/div/div[1]',
        ).text
    except Exception:
        current_company = ""

    basic_data["user_name"] = (user_name,)
    basic_data["user_location"] = user_location
    basic_data["user_description"] = user_description
    basic_data["current_company"] = current_company

    return basic_data


def get_data_from_google(role: str) -> None:
    """
    This function is the main function of this BOT.
    here we search the required role on google and get results (profile links).
    then after, we iterate over each result and get linkedin profile data.

    Args:
        role: (str) - the role we required to get profiles on.
    Returns:
        None
    """
    # start time is noted here.
    start_time = time.time()
    
    # the list which contains whole profile data. 
    total_data = []
    
    # this search url is very specific.
    # here we only get results from linkedin
    # and also the results are in english language and from India.
    url = f"{role} site:linkedin.com/in -jobs"
    only_english = "language:en"
    only_indians = "location:In"
    search_url = "https://www.google.com/search?q=" + url + only_english + only_indians
    
    # here we are using headless driver
    # beacuse it is faster and efficient.
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    
    # sending request with seacrh url
    driver.get(search_url)
    
    # wait function - which is given 10 secs to wait , when called.
    wait = WebDriverWait(driver, 10)
    
    # this is a Flag which says that, does the particular page has a next button for pagintion.
    next_exists = True

    # until the page contains a next button we execute code in while block.
    while next_exists:

        try:
            linkedin_links = wait.until(
                EC.visibility_of_all_elements_located(
                    (
                        By.XPATH,
                        '//*[@id="rso"]/div/div/div/div/div/a',
                    )
                )
            )
        except Exception:
            # this is to handle the case, when driver is not able to locate 
            # profile links on google search results page.
            next_exists = False
            continue
        
        # iterating over each profile link
        for link in linkedin_links:

            user_data = {
                "name": None,
                "role": None,
                "currently_doing": None,
                "current_company": None,
                "about": None,
                "linkedin_profile": None,
                "location": None,
                "experience": None,
                "certifications": None,
                "projects": None,
            }

            try:
                user_data["linkedin_profile"] = link.get_attribute("href")
                link.click()

                wait.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="main-content"]/section[1]/div/section/section[1]/div/div[1]/img',
                        )
                    )
                )
                user_details = driver.find_element(
                    By.XPATH,
                    '//*[@id="main-content"]/section[1]/div/section/section[1]/div/div[2]/div[1]',
                )
            except Exception:
                # this is to handle the case, when we driver is not able to locate a profile link or 
                # getting a profile link without any hyperlink. 
                continue

            basic_data = get_basic_details(user_details)

            try:
                user_has_sections = user_details.find_element(
                    By.XPATH,
                    '//*[@id="main-content"]/section/div/section/section',
                ).is_displayed()
            except Exception:
                continue
            
            # accessing all the sections in the profile page
            if user_has_sections:
                sections = user_details.find_elements(
                    By.XPATH, '//*[@id="main-content"]/section/div/section/section'
                )

                # iterating over each section.
                for section in sections:
                    section_name = section.get_attribute("class")
                    section_html = section.get_attribute("outerHTML")

                    # for getting the whole html of the section, we use bs4.
                    section_soup = BeautifulSoup(section_html, "html.parser")

                    if "summary" in section_name:
                        about = get_about(section_soup)
                        user_data["about"] = about
                    if "experience" in section_name:
                        experiences = get_experience(section_soup)
                        user_data["experience"] = experiences
                    if "projects" in section_name:
                        projects = get_projects(section_soup)
                        user_data["projects"] = projects
                    if "certifications" in section_name:
                        certifications = get_certification(section_soup)
                        user_data["certifications"] = certifications

            user_data["name"] = basic_data["user_name"][0]
            user_data["currently_doing"] = basic_data["user_description"]
            user_data["location"] = basic_data["user_location"]
            user_data["current_company"] = basic_data["current_company"]
            user_data["role"] = role

            # adding all the profile data into a list.
            total_data.append(user_data)

            # going back to google results page so that we could pick the next profile link.
            driver.back()

        # check whether the current page has a "next" button for pagination.  
        next_exists = driver.find_element(By.ID, "pnnext").is_displayed()
        if next_exists:
            next_page = driver.find_element(By.XPATH, '//*[@id="pnnext"]')
            next_page.click()

    # always need to quit the driver at the end.
    driver.quit()

    end_time = time.time()

    # total time for completing the execution.
    print("total time taken: ", end_time - start_time)

    # saving the data in excel sheet.
    df = pandas.DataFrame(total_data)
    df.to_excel(f"{role}linkedProfiles.xlsx")
    print("saved into file successfully")


if __name__ == "__main__":
    role = "python developer"
    get_data_from_google(role="flutter developer", need_jobs=False)
