#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import platform
import random
import time

import requests
import undetected_chromedriver as uc
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

USERNAME = ""
PASSWORD = ""
BARK_KEY = "" 

def submit_course_and_notify(driver, course_id):
    """
    Submit the course in the current tab and send a push notification.
    
    :param driver: Selenium WebDriver instance.
    :param course_id: The course ID for the notification message.
    """
    try:
        # Navigate to the course submission page (replace with the actual URL)
        submission_url = "https://banner.apps.uillinois.edu/StudentRegistrationSSB/ssb/term/termSelection?mode=registration"
        driver.get(submission_url)
        print("Navigated to course submission page")
        time.sleep(1)

        actions = ActionChains(driver)

        # Select the term dropdown and click it
        term_dropdown = driver.find_element(By.XPATH, '//*[@id="s2id_txt_term"]/a/span[2]')
        actions.move_to_element(term_dropdown).click().perform()
        time.sleep(1)

        # Choose the specified term (XPath might need to be adjusted)
        term_option = driver.find_element(By.XPATH, '//*[@id="120251"]')
        actions.move_to_element(term_option).click().perform()
        time.sleep(1)

        # Click the continue button
        continue_button = driver.find_element(By.XPATH, '//*[@id="term-go"]')
        actions.move_to_element(continue_button).click().perform()
        time.sleep(1)

        # Switch to the plans tab
        plans_tab = driver.find_element(By.XPATH, '//*[@id="loadPlans-tab"]')
        actions.move_to_element(plans_tab).click().perform()
        print("Navigated to plans page")
        time.sleep(2)

        # Click the 'add all' button in the plan accordion
        add_all_button = driver.find_element(By.XPATH, '//*[@id="planAccordion"]/div[1]/div/button')
        actions.move_to_element(add_all_button).click().perform()
        time.sleep(1)

        # Click the save button to submit the course
        save_button = driver.find_element(By.XPATH, '//*[@id="saveButton"]')
        actions.move_to_element(save_button).click().perform()

        # Send push notification
        send_notification(f"Course {course_id} submitted")
    except Exception as e:
        error_message = f"An error occurred during course submission: {e}"
        print(error_message)
        send_notification(error_message)


def send_notification(message):
    """
    Send a push notification via the Bark API.
    
    :param message: The message content to be sent.
    """
    url = f"https://api.day.app{BARK_KEY}/"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "charset": "utf-8",
    }
    payload = f"body={message}"
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            print("Bark notification sent successfully.")
        else:
            print(f"Bark notification failed with status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending Bark notification: {e}")


def get_chrome_profile_path():
    """
    Get the Chrome user data directory and profile directory.
    
    :return: tuple(user_data_dir, profile_dir)
    :raises Exception: if the operating system is unsupported.
    """
    os_name = platform.system()
    if os_name == "Windows":
        user_data_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data")
        profile_dir = "Default"
    elif os_name == "Darwin":
        user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        profile_dir = "Profile 2"
    else:
        raise Exception("Unsupported operating system.")
    return user_data_dir, profile_dir


def monitor_ajax_and_submit_course():
    """
    Continuously monitor seat availability via AJAX responses.
    If no seats are available, wait for a random interval before retrying.
    Once a seat is available, automatically submit the course and send a notification.
    """
    # Configure Chrome performance logging
    capabilities = DesiredCapabilities.CHROME
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}

    # Get Chrome user data directory and profile directory
    user_data_dir, profile_dir = get_chrome_profile_path()

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--profile-directory={profile_dir}")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = uc.Chrome(options=options, desired_capabilities=capabilities)

    try:
        def perform_login():
            """
            Perform the login sequence:
            1. Log out.
            2. Navigate to the registration page.
            3. Click the login link.
            4. If login is required, input the password (username input is commented out).
            """
            driver.get("https://experience.elluciancloud.com/logout")
            time.sleep(2)
            driver.get("https://banner.apps.uillinois.edu/StudentRegistrationSSB/ssb/registration?mepCode=1UIUC")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="collegeSchedulerLink"]/span'))
            )
            login_link = driver.find_element(By.XPATH, '//*[@id="collegeSchedulerLink"]/span')
            login_link.click()
            print("Login link clicked.")

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="netid"]'))
                )
                print("Login required. Proceeding to login.")

                # Uncomment below if username input is required
                # username_field = driver.find_element(By.XPATH, '//*[@id="netid"]')
                # username_field.send_keys(USERNAME)

                password_field = driver.find_element(By.XPATH, '//*[@id="easpass"]')
                # Ensure PASSWORD is set correctly before uncommenting the next line
                # password_field.send_keys(PASSWORD)
                time.sleep(1)
                password_field.send_keys(Keys.RETURN)

                WebDriverWait(driver, 15).until(
                    EC.url_contains("https://illinois.collegescheduler.com/")
                )
                print("Login successful.")
            except Exception:
                print("Already logged in or no login required.")

        def click_generate_schedule_button():
            """
            Click the 'Generate' button to trigger the AJAX request.
            """
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="schedules_panel"]/div[1]/button/span[2]/span')
                )
            )
            generate_button = driver.find_element(By.XPATH, '//*[@id="schedules_panel"]/div[1]/button/span[2]/span')
            generate_button.click()
            print("Generate button clicked.")

        def uncheck_checkboxes():
            """
            Uncheck the checkboxes and click the OK button on the popup.
            """
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="scheduler-app"]/div/main/div/div/div[3]/div[1]/div[2]/table/thead/tr/th[1]',
                    )
                )
            )
            checkbox = driver.find_element(
                By.XPATH,
                '//*[@id="scheduler-app"]/div/main/div/div/div[3]/div[1]/div[2]/table/thead/tr/th[1]',
            )
            checkbox.click()
            print("Checkbox unchecked.")

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div/div[2]/div/div/div[2]/button'))
            )
            time.sleep(0.5)
            ok_button = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div/div[2]/button')
            ok_button.click()
            print("OK button clicked.")

        def fetch_ajax_response():
            """
            Extract AJAX response content from the browser's performance logs.
            
            :return: Parsed JSON data if found, otherwise None.
            """
            time.sleep(1)
            browser_logs = driver.get_log("performance")
            events = [
                json.loads(entry["message"])["message"]
                for entry in browser_logs
                if "Network.responseReceived" in json.loads(entry["message"])["message"]["method"]
            ]

            target_events = [
                event
                for event in events
                if "schedules/generate" in event.get("params", {}).get("response", {}).get("url", "")
            ]
            if not target_events:
                return None

            last_event = target_events[-1]
            request_id = last_event["params"]["requestId"]
            response_body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            return json.loads(response_body["body"])

        # Initialize login and uncheck process
        perform_login()
        uncheck_checkboxes()

        while True:
            click_generate_schedule_button()
            result = fetch_ajax_response()

            if not result or "sections" not in result:
                print("No data found. Retrying after relogin.")
                send_notification("No data found. Retrying after relogin.")
                perform_login()
                uncheck_checkboxes()
                continue

            sections = result["sections"]
            if sections:
                available_seats = sections[0].get("openSeats", -1)
                course_id = sections[0].get("id", 0)
                if available_seats > 0:
                    print(f"Seats available: {available_seats}")
                    send_notification(f"Seats available: {available_seats} for course ID {course_id}")
                    perform_login()
                    submit_course_and_notify(driver, course_id)
                    break
                else:
                    print(f"openSeats: {available_seats}")
                    print("No seats available.")
            else:
                print("Sections data not found.")

            # Wait for a random interval between 10 and 140 seconds before retrying
            wait_time = random.randint(10, 140)
            print(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    monitor_ajax_and_submit_course()
