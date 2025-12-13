from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

TEST_EVENT_TITLE = "N/A"  # Non-Rangers event that can be changed to test functionality when no Rangers games are available
EVENTS_URL = "https://chasegetsyoucloser.com/madison-square-garden/"
REFRESH_INTERVAL_SECONDS = 10
CREDENTIALS_PATH = Path("credentials.txt")
PLACEHOLDER_TEXT = "<insert here>"


def load_credentials(path: Path = CREDENTIALS_PATH):
    """
    Read email/password from a local text file with lines formatted as:
    EMAIL: value
    PASSWORD: value
    """
    email = password = None

    with path.open() as cred_file:
        for raw_line in cred_file:
            line = raw_line.strip()
            if not line or ":" not in line:
                continue
            key, value = [part.strip() for part in line.split(":", 1)]
            key = key.lower()
            if key == "email":
                email = value
            elif key == "password":
                password = value

    return email, password


def scrape_chase(email, password):
    """
    Opens the Chase Lounge login page, fills out login page, navigates to MSG events, 
    and continually checks for available NYR events to reserve.
    """

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    driver.get("https://chasegetsyoucloser.com/login")

    wait = WebDriverWait(driver, 15)

    try:
        # Log in to chasegetsyoucloser.com account
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(0.2)

        email_box = wait.until(EC.element_to_be_clickable((By.ID, "email")))
        email_box.clear()
        email_box.send_keys(email)

        password_box = wait.until(EC.element_to_be_clickable((By.ID, "password")))
        password_box.clear()
        password_box.send_keys(password)

        privacy_box = wait.until(EC.element_to_be_clickable((By.ID, "agreeToPrivacy")))
        privacy_box.click()

        terms_box = wait.until(EC.element_to_be_clickable((By.ID, "agreeToTerms")))
        terms_box.click()

        login_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        login_button.click()
        print("Login submitted")
        time.sleep(1)

        # Navigate to Madison Square Garden events page
        msg_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a[data-pt-name="Reserve Madison Square Garden"]')
            )
        )
        msg_btn.click()
        print("Opened Madison Square Garden reservation page")

        # Main loop to find open Rangers events
        while True:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table")))
            rows = driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
            print(f"Found {len(rows)} events on the page.")

            for row in rows:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
                    time.sleep(0.2)

                    title_elem = row.find_element(By.CSS_SELECTOR, "span[style*='font-weight:bold']")
                    event_title = title_elem.text.strip()
                    is_rangers_game = "New York Rangers" in event_title
                    is_test_event = event_title == TEST_EVENT_TITLE

                    if not (is_rangers_game or is_test_event):
                        continue
                    print(f"Found target event: {event_title}")

                    button = row.find_element(By.CSS_SELECTOR, "a.js-reserve")
                    btn_classes = button.get_attribute("class")
                    btn_text = button.text.strip().lower()

                    if "btn-primary" in btn_classes and btn_text == "reserve":
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(0.1)
                        print("Blue Reserve button found. Clicking to start reservation…")
                        button.click()
                        if complete_reservation_form(driver):
                            print("Reservation completed; reloading event list to continue monitoring.")
                            driver.get(EVENTS_URL)
                            break
                        print("Reservation not completed; continuing to next event.")
                        continue
                    else:
                        print("Rangers game found but button not available for reservation")

                except Exception as e:
                    print(f"Error reading row: {e}")

            else: #Reached end of list, iterate again after refresh
                print("No AVAILABLE Rangers events found. Refreshing to check again soon…")
                time.sleep(REFRESH_INTERVAL_SECONDS)
                driver.get(EVENTS_URL)
                continue
            
            # Successful reservation, already reloaded the page; loop again.
            continue

    except Exception as e:
        print(f"ERROR: {e}")
        return driver


def complete_reservation_form(driver):
    """
    Set quantity to 2 and submit the modal if allowed; otherwise close it.
    """
    modal = None
    try:
        modal = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "reserve-modal"))
        )

        qty_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "numTickets"))
        )
        select = Select(qty_select)
        option_two = next(
            (opt for opt in select.options if opt.get_attribute("value") == "2"),
            None,
        )

        if not option_two or not option_two.is_enabled():
            print("Quantity 2 is not available. Closing the modal.")
            close_modal(modal)
            return False

        select.select_by_value("2")
        print("Quantity changed to 2 tickets.")

        reserve_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "reserve-modal-submit"))
        )

        if not reserve_button.is_enabled():
            print("Reserve button is disabled. Closing the modal.")
            close_modal(modal)
            return False

        reserve_button.click()
        print("Clicked the modal's Reserve button. Waiting for confirmation…")

        if confirm_reservation(driver):
            print("Reservation confirmed.")
            return True

        print("Confirmation dialog did not appear. Assuming failure.")
        return False

    except Exception as e:
        print(f"Failed to submit reservation modal: {e}")
        close_modal(modal if "modal" in locals() else None)
        return False


def close_modal(modal):
    if not modal:
        return
    try:
        close_button = modal.find_element(By.CSS_SELECTOR, "[data-bs-dismiss='modal']")
        if close_button.is_enabled():
            close_button.click()
            print("Modal closed.")
    except Exception as close_error:
        print(f"Could not close modal cleanly: {close_error}")


def confirm_reservation(driver):
    """
    Handle the SweetAlert confirmation dialog.
    """
    try:
        confirm_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".swal2-container .swal2-confirm"))
        )
        confirm_button.click()
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
        )
        print("SweetAlert confirmation acknowledged.")
        return True
    except TimeoutException:
        print("Timed out waiting for confirmation dialog.")
        return False
    except Exception as e:
        print(f"Unexpected error while confirming reservation: {e}")
        return False


if __name__ == "__main__":
    email, password = load_credentials()
    scrape_chase(email, password)
