from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def scrape_chase(email, password):
    """
    Opens the Chase Lounge login page, scrolls once to reveal checkboxes,
    logs in, opens the MSG venue page, scans for New York Rangers events,
    and clicks the first available blue 'Reserve' button.
    """

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    driver.get("https://chasegetsyoucloser.com/login")

    wait = WebDriverWait(driver, 15)

    try:
        # Scroll slightly to reveal checkboxes
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(0.2)

        # Fill email + password
        email_box = wait.until(EC.element_to_be_clickable((By.ID, "email")))
        email_box.clear()
        email_box.send_keys(email)

        password_box = wait.until(EC.element_to_be_clickable((By.ID, "password")))
        password_box.clear()
        password_box.send_keys(password)

        # Check the required boxes
        privacy_box = wait.until(EC.element_to_be_clickable((By.ID, "agreeToPrivacy")))
        privacy_box.click()

        terms_box = wait.until(EC.element_to_be_clickable((By.ID, "agreeToTerms")))
        terms_box.click()

        # Submit login
        login_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        login_button.click()
        print("Login submitted")

        # Allow redirect
        time.sleep(1)

        # Click MSG "Reserve Now"
        msg_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a[data-pt-name="Reserve Madison Square Garden"]')
            )
        )
        msg_btn.click()
        print("Opened Madison Square Garden reservation page")

        # --- WAIT FOR EVENT TABLE ---
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table")))

        # Get all table rows
        rows = driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
        print(f"Found {len(rows)} events on the page.")

        # Loop through each event row
        for row in rows:
            try:
                title_elem = row.find_element(By.CSS_SELECTOR, "span[style*='font-weight:bold']")
                event_title = title_elem.text.strip()

                if event_title.startswith("New York Rangers vs"):
                    print(f"Found Rangers game: {event_title}")

                    # Find the reserve/waitlist button
                    button = row.find_element(By.CSS_SELECTOR, "a.js-reserve")
                    btn_classes = button.get_attribute("class")

                    # Skip red waitlist buttons
                    if "btn-danger" in btn_classes:
                        print("This Rangers game is waitlisted (red button). Skipping.")
                        continue

                    # Otherwise, it's available ("Reserve" or "Modify", but blue/green)
                    print("This Rangers game is AVAILABLE! Clicking reserve…")
                    button.click()
                    return driver

            except Exception as e:
                print(f"Error reading row: {e}")

        print("No AVAILABLE Rangers events found.")

        return driver

    except Exception as e:
        print(f"ERROR: {e}")
        return driver



if __name__ == "__main__":
    EMAIL = "jblukin@hotmail.com"
    PASSWORD = "JBLcr2014!!!"
    scrape_chase(EMAIL, PASSWORD)
