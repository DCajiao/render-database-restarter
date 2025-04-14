import logging
import random
import string
import time
from datetime import datetime, timedelta, timezone

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

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
    """
    Launch an undetected Chrome browser with headless configuration.

    Returns:
        webdriver.Chrome: A Selenium WebDriver instance with stealth settings.
    """
    try:
        logger.debug("Starting undetected browser")
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
        logger.debug("✔ Browser started")
        return driver
    except Exception as e:
        logger.error(f"Error starting undetected browser: {e}")
        return None


def close_browser(driver):
    """
    Safely closes the browser instance.

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver to be closed.
    """
    #TODO: I have an issue with closing the browser, it doesn't close properly
    try:
        driver.quit()
        logger.debug("✔ Browser closed")
    except Exception as e:
        logger.error(f"Error closing browser: {e}")

# ---------- LOGIN SCRAPING ----------
def render_login():
    """
    Logs into the Render dashboard using credentials from environment variables.

    Args:
        driver (webdriver.Chrome): An initialized WebDriver instance.

    Returns:
        webdriver.Chrome: The logged-in WebDriver instance.

    Raises:
        ValueError: If required environment variables are missing.
        RuntimeError: If the browser could not be started.
    """
    credentials = credentials_management.load_credentials()
    if not credentials['EMAIL'] or not credentials['PASSWORD']:
        logger.error(
            "❌ These environment variables are required: RENDER_EMAIL, RENDER_PASSWORD")
        raise ValueError(
            "❌ Missing environment variables: RENDER_EMAIL, RENDER_PASSWORD")
    logger.debug("✅ Environment variables loaded")

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
        logger.debug("🔄 Loading login page...")

        # Wait for email input to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        logger.debug("🔄 Page loaded")

        # Fill fields
        email_input = driver.find_element(By.NAME, "email")
        email_input.send_keys(credentials['EMAIL'])
        logger.debug("🔄 Email filled")
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(credentials['PASSWORD'])
        logger.debug("🔄 Password filled")

        # Click on "Sign in" button
        login_button = driver.find_element(
            By.CSS_SELECTOR, '[data-test-id="signin-submit-button"]')
        login_button.click()
        logger.debug("🔄 Sending credentials...")

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


def render_logout(driver):
    """
    Logs out the current user from the Render dashboard.

    Args:
        driver (webdriver.Chrome): The logged-in WebDriver instance.
    """
    # TODO: FIX THIS FUNCTION
    try:
        # Click on the user icon to open the dropdown menu
        user_icon = driver.find_element(
            By.CSS_SELECTOR, '[data-test-id="user-icon"]')
        user_icon.click()

        # Wait for the logout button to appear and click it
        logout_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[@data-test-id='logout-button']"))
        )
        logout_button.click()

        logger.info("✅ Successfully logged out!")
    except Exception as e:
        logger.error(f"❌ Error during logout: {e}")


def go_to_dashboard(driver):
    """
    Navigates to the main Render dashboard page and waits for it to fully load.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.

    Returns:
        webdriver.Chrome: The same instance, now on the dashboard page.
    """
    try:
        logger.debug("🔄 Navigating to the Render dashboard...")
        driver.get(definitions.RENDER_URL)

        # Wait for the dashboard to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
        )
    except TimeoutError:
        logger.error("❌ Timeout error: Dashboard page took too long to load.")
    except Exception as e:
        logger.error(f"❌ Error during navigation: {e}")
    finally:
        return driver

# ---------- CREATE NEW DATABASE SCRAPING ----------
def create_new_database(driver):
    """
    Creates a new PostgreSQL database using Render's UI.

    Navigates to the database creation page, fills the form, and submits it using default settings.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.

    Returns:
        str: The name of the newly created database.
    """

    # Navigate to the "Create New Database" page
    driver.get(definitions.RENDER_CREATE_NEW_DATABASE_URL)

    wait = WebDriverWait(driver, 15)

    # Wait for the database name input field to appear
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, '[data-test-id="new-database-name-field"]')))

    # Generate a unique database name
    db_name = "auto-db-" + \
        ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    # Fill in the database name
    name_input = driver.find_element(
        By.CSS_SELECTOR, '[data-test-id="new-database-name-field"]')
    name_input.send_keys(db_name)

    # Select PostgreSQL version (optional, default to 16)
    # version_select = driver.find_element(By.ID, "version")
    # version_select.click()
    # option_16 = version_select.find_element(By.XPATH, ".//option[@value='16']")
    # option_16.click()

    # Wait for the "Free" plan button and click it
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//button[@name='Free']")))
    free_plan_button = driver.find_element(By.XPATH, "//button[@name='Free']")
    free_plan_button.click()

    # Submit the form to create the database
    submit_button = driver.find_element(
        By.CSS_SELECTOR, '[data-test-id="new-database-submit-button"]')
    submit_button.click()

    print(f"✅ Database '{db_name}' creation initiated.")

    return db_name

# ---------- GET ACTIVE DATABASES ----------
def get_active_databases(driver) -> list[dict]:
    """
    Retrieves a list of currently active PostgreSQL 16 databases from the Render dashboard.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.

    Returns:
        list[dict]: A list of dictionaries with keys: name, status, runtime, region, deployed_at.
    """

    logger.info("🔄 Getting active databases...")

    # Navigate to the main dashboard page
    driver = go_to_dashboard(driver)

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
            name_element = row.find_element(
                By.CSS_SELECTOR, "td:nth-child(3) a span")
            name = name_element.text.strip()

            # Extract the 'Status' text
            status_element = row.find_element(
                By.CSS_SELECTOR, "td:nth-child(4) span[title]")
            status = status_element.get_attribute("title")

            # Extract the 'Runtime' text
            runtime_element = row.find_element(
                By.CSS_SELECTOR, "td:nth-child(5) span[title]")
            runtime = runtime_element.get_attribute("title")

            # Extract the 'Region' text
            region_element = row.find_element(
                By.CSS_SELECTOR, "td:nth-child(6)")
            region = region_element.text.strip()

            # Extract the 'Deployed Time' ISO value
            deployed_element = row.find_element(
                By.CSS_SELECTOR, "td:nth-child(7) time")
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
            continue

    return databases


def get_database_status(driver, db_name: str) -> dict:
    """
    Get the usage status of a specific Render PostgreSQL database.
    This includes time since deployment, remaining time before expiration (750h limit),
    and storage usage percentage.

    Args:
        driver (webdriver.Chrome): The active browser session.
        db_name (str): Name of the database.

    Returns:
        dict: {
            'deployed_at': str (ISO timestamp),
            'hours_used': float,
            'hours_left': float,
            'percentage_used': float,
            'estimated_expiration': str (UTC datetime),
            'storage_used_percent': float
        }
    """
    logger.debug(f"🔍 Checking status for database '{db_name}'...")

    # Retrieve the list of active databases using the existing driver session
    databases = get_active_databases(driver)
    db = next((d for d in databases if d["name"].lower() == db_name.lower()), None)

    if not db:
        logger.error(f"❌ Database '{db_name}' not found.")
        raise ValueError(f"Database '{db_name}' not found.")

    # Parse deployment time
    deployed_at = db["deployed_at"]
    deployed_dt = datetime.fromisoformat(deployed_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)


    hours_used = (now - deployed_dt).total_seconds() / 3600
    hours_left = max(0, definitions.DB_MAX_HOURS - hours_used)
    percentage_used = min(100, (hours_used / definitions.DB_MAX_HOURS) * 100)
    estimated_expiration = deployed_dt + timedelta(hours=definitions.DB_MAX_HOURS)

    driver = go_to_dashboard(driver)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
    )

    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    target_link = None

    for row in rows:
        try:
            name_el = row.find_element(By.CSS_SELECTOR, "td:nth-child(3) a span")
            name = name_el.text.strip()
            if name.lower() == db_name.lower():
                target_link = row.find_element(By.CSS_SELECTOR, "td:nth-child(3) a")
                break
        except:
            continue

    if not target_link:
        logger.error(f"❌ Could not find link to database '{db_name}'")
        raise ValueError(f"Could not locate link for database '{db_name}'")

    target_link.click()

    # Wait for the page to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "general"))
    )

    # Extract the text of the "Storage Used" element
    try:
        storage_info = driver.find_element(
            By.XPATH, "//div[@aria-label='storage used']//div[contains(@class, 'font-semibold')]"
        ).text
        storage_used_percent = float(storage_info.split('%')[0])/100
    except Exception as e:
        logger.warning(f"⚠️ Could not extract storage percentage: {e}")
        storage_used_percent = None


    return {
        "deployed_at": deployed_at,
        "hours_used": round(hours_used, 2),
        "hours_left": round(hours_left, 2),
        "percentage_used": round(percentage_used, 2),
        "estimated_expiration": estimated_expiration.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "storage_used_percent": storage_used_percent,
    }

# ---------- GET DATABASE CREDENTIALS ----------
def get_active_database_credentials(driver, db_name: str) -> dict:
    """
    Fetches connection credentials of a specified database.

    Navigates to the database detail page, reveals hidden secrets, and scrapes all fields.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
        db_name (str): The exact name of the database to search for.

    Returns:
        dict: A dictionary with credentials, including:
            - hostname
            - port
            - database
            - username
            - password
            - internal_url
            - external_url
            - psql_command

    Raises:
        ValueError: If the database name is not found.
    """

    logger.debug(f"🔄 Getting credentials for active database '{db_name}'...")

    # Navigate to the main dashboard page
    driver = go_to_dashboard(driver)

    # Wait for the table body to load completely
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
    )

    # Select all rows within the table and find the target link
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    target_link = None

    for row in rows:
        try:
            name_el = row.find_element(
                By.CSS_SELECTOR, "td:nth-child(3) a span")
            name = name_el.text.strip()
            if name.lower() == db_name.lower():
                target_link = row.find_element(
                    By.CSS_SELECTOR, "td:nth-child(3) a")
                break
        except NoSuchElementException:
            continue

    if not target_link:
        msg = f"❌ The database '{db_name}' does not exist or is not available."
        logger.error(msg)
        raise ValueError(msg)

    # Click on the target link to enter the database detail page
    target_link.click()

    # Wait for the page to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "connections"))
    )

    # Click on the button to show the database credentials (Hide/Show)
    show_buttons = driver.find_elements(
        By.CSS_SELECTOR, "button[aria-label='Show secret']")
    for btn in show_buttons:
        try:
            btn.click()
        except:
            pass  # Ignore if the button is not clickable

    # Get the database credentials
    def get_input_value(id_):
        try:
            return driver.find_element(By.ID, id_).get_attribute("value")
        except NoSuchElementException:
            return None

    credentials = {
        "hostname": get_input_value("database-hostname"),
        "port": get_input_value("database-port"),
        "database": get_input_value("database-name"),
        "username": get_input_value("database-username"),
        "password": get_input_value("database-password"),
        "internal_url": get_input_value("internal-database-url"),
        "external_url": get_input_value("external-database-url"),
        "psql_command": get_input_value("psql-command"),
    }

    return credentials

# ---------- DELETE DATABASE ----------
def delete_active_database(driver, db_name: str) -> None:
    """
    Deletes a specific database from the Render dashboard.

    Navigates to the database detail view, scrolls to the bottom, triggers the delete modal,
    fills the confirmation command, and submits the deletion.

    Args:
        driver (webdriver.Chrome): The WebDriver instance.
        db_name (str): The name of the database to delete.

    Returns:
        None

    Raises:
        ValueError: If the target database is not found on the dashboard.
    """

    logger.info(f"🔄 Deleting active database '{db_name}'...")

    # Navigate to the main dashboard page
    driver = go_to_dashboard(driver)

    # Wait for the table body to load completely
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody"))
    )

    # Find the target database link
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    target_link = None

    for row in rows:
        try:
            name_el = row.find_element(
                By.CSS_SELECTOR, "td:nth-child(3) a span")
            name = name_el.text.strip()
            if name.lower() == db_name.lower():
                target_link = row.find_element(
                    By.CSS_SELECTOR, "td:nth-child(3) a")
                break
        except:
            continue

    if not target_link:
        msg = f"❌ The database '{db_name}' does not exist or is not available."
        logger.error(msg)
        raise ValueError(msg)

    target_link.click()

    # Wait for the page to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "connections"))
    )

    # Scroll down to the bottom of the page to load the "Delete" button
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait for the "Delete" button to be clickable
    delete_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Delete')]"))
    )
    delete_button.click()

    # Wait for the confirmation modal to appear
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "confirm-delete"))
    )

    # Extract the text from the confirmation modal
    confirm_text_el = driver.find_element(
        By.XPATH,
        "//form[@id='confirm-delete']//span[contains(@class, 'status-critical-text')]"
    )
    confirm_text = confirm_text_el.text.strip()

    # Write the confirmation text in the input field
    input_el = driver.find_element(By.ID, "sudo-command")
    input_el.send_keys(confirm_text)

    # Wait for the "Confirm" button to be clickable
    confirm_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-testid='confirm-delete-button']"))
    )
    confirm_btn.click()

    logger.info(f"✅ Database '{db_name}' deletion initiated.")
