import logging
import random
import string

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

import utils.definitions as definitions
import utils.credentials_management as credentials_management

#### ---------- LOGGING ---------- ####
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ---------- CHROME HEADLESS CONFIGURATION ----------
def start_browser():
    try:
        logger.info("Starting undetected browser")
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--lang=en-US')

        driver = uc.Chrome(options=options, headless=False)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("✔ Browser started")
        return driver
    except Exception as e:
        logger.error(f"Error starting undetected browser: {e}")
        return None

def close_browser(driver):
    try:
        driver.quit()
        logger.info("✔ Browser closed")
    except Exception as e:
        logger.error(f"Error closing browser: {e}")

# ---------- LOGIN SCRAPING ----------
def render_login(driver):
    #### ---------- ENV VARIABLES ---------- ####
    # -> EMAIL, PASSWORD
    credentials = credentials_management.load_credentials()
    if not credentials['EMAIL'] or not credentials['PASSWORD']:
        logger.error(
            "❌ These environment variables are required: RENDER_EMAIL, RENDER_PASSWORD")
        raise ValueError(
            "❌ Missing environment variables: RENDER_EMAIL, RENDER_PASSWORD")
    logger.info("✅ Environment variables loaded")

    #### ---------- STARTING BROWSER ---------- ####
    driver = start_browser()
    if driver is None:
        msg = "❌ Error starting undetected browser"
        logger.error(msg)
        raise RuntimeError(msg)

    #### ---------- SCRAPING RENDER DASHBOARD ---------- ####
    try:
        # Go to Render login page
        driver.get(definitions.RENDER_LOGIN_URL)
        logger.info("🔄 Loading login page...")

        # Wait for email input to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        logger.info("🔄 Page loaded")

        # Fill fields
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys(credentials['EMAIL'])
        logger.info("🔄 Email filled")
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(credentials['PASSWORD'])
        logger.info("🔄 Password filled")

        # Click on "Sign in" button
        login_button = driver.find_element(
            By.CSS_SELECTOR, '[data-test-id="signin-submit-button"]')
        login_button.click()
        logger.info("🔄 Sending credentials...")

        # Wait for redirection (check that we are no longer on the login page)
        WebDriverWait(driver, 15).until_not(
            EC.url_contains("/login")
        )

        logger.info("✅ Successfully logged in!")
        return driver
    except TimeoutError:
        logger.error("❌ Timeout error: Login page took too long to load.")
    except Exception as e:
        logger.error(f"❌ Error during login: {e}")
    # finally:
    #     driver.quit()

def render_logout(driver):
    # TODO: FIX THIS FUNCTION
    try:
        # Click on the user icon to open the dropdown menu
        user_icon = driver.find_element(By.CSS_SELECTOR, '[data-test-id="user-icon"]')
        user_icon.click()

        # Wait for the logout button to appear and click it
        logout_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@data-test-id='logout-button']"))
        )
        logout_button.click()

        logger.info("✅ Successfully logged out!")
    except Exception as e:
        logger.error(f"❌ Error during logout: {e}")

# ---------- CREATE NEW DATABASE SCRAPING ----------
def create_new_database(driver):
    # Navigate to the "Create New Database" page
    driver.get(definitions.RENDER_CREATE_NEW_DATABASE_URL)

    wait = WebDriverWait(driver, 15)

    # Wait for the database name input field to appear
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="new-database-name-field"]')))

    # Generate a unique database name
    db_name = "auto-db-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    # Fill in the database name
    name_input = driver.find_element(By.CSS_SELECTOR, '[data-test-id="new-database-name-field"]')
    name_input.send_keys(db_name)

    # Select PostgreSQL version (optional, default to 16)
    # version_select = driver.find_element(By.ID, "version")
    # version_select.click()
    # option_16 = version_select.find_element(By.XPATH, ".//option[@value='16']")
    # option_16.click()

    # Wait for the "Free" plan button and click it
    wait.until(EC.presence_of_element_located((By.XPATH, "//button[@name='Free']")))
    free_plan_button = driver.find_element(By.XPATH, "//button[@name='Free']")
    free_plan_button.click()

    # Submit the form to create the database
    submit_button = driver.find_element(By.CSS_SELECTOR, '[data-test-id="new-database-submit-button"]')
    submit_button.click()

    print(f"✅ Database '{db_name}' creation initiated.")

    return db_name

# ---------- GET ACTIVE DATABASES ----------
def get_active_databases(driver) -> list[dict]:
    """
    Extract the list of active databases from the main dashboard.

    Args:
        driver (Page): The Playwright Page instance currently on the dashboard.

    Returns:
        list[dict]: A list of dictionaries, each representing a database with its metadata.
    """
    # Navigate to the main dashboard page
    driver.get(definitions.RENDER_URL)

    # Wait for the table body to load completely
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
    )

    # Select all rows within the table
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    databases = []

    for row in rows:
        try:
            # Extract the 'Service Name' text
            name_element = row.find_element(By.CSS_SELECTOR, "td:nth-child(3) a span")
            name = name_element.text.strip()

            # Extract the 'Status' text
            status_element = row.find_element(By.CSS_SELECTOR, "td:nth-child(4) span[title]")
            status = status_element.get_attribute("title")

            # Extract the 'Runtime' text
            runtime_element = row.find_element(By.CSS_SELECTOR, "td:nth-child(5) span[title]")
            runtime = runtime_element.get_attribute("title")

            # Extract the 'Region' text
            region_element = row.find_element(By.CSS_SELECTOR, "td:nth-child(6)")
            region = region_element.text.strip()

            # Extract the 'Deployed Time' ISO value
            deployed_element = row.find_element(By.CSS_SELECTOR, "td:nth-child(7) time")
            deployed = deployed_element.get_attribute("datetime")

            # Only include databases that are actually running/active
            if name and status and status.lower() in ["available", "deployed"] and runtime.lower() == "postgresql 16":
                databases.append({
                    "name": name,
                    "status": status,
                    "runtime": runtime,
                    "region": region,
                    "deployed_at": deployed,
                })

        except Exception as e:
            logger.warning(f"❌ Error extracting service info: {e}")
            continue

    return databases
