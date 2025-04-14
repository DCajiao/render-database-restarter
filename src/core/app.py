# -*- coding: utf-8 -*-
# This file contains the main application logic for the web scraping tool.

import time
import logging

import core.scrapper as scrapper


#### ---------- LOGGING ---------- ####
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

### ---------  LIST OF FEATURES --------- ###
def migration_status():
    """
    Check the migration status of the database.
    """
    logger.info("🔄 Checking migration status...")

    # Check if there are any active databases

    # Initialize the scraper
    driver = scrapper.go_to_dashboard(scrapper.render_login())
    
    try:
        databases = scrapper.get_active_databases(driver)
        if len(databases) > 0:
            database_name = databases[0]['name']
            logger.info(f"✅ Active database found: {database_name}")
            pass
        else:
            logger.info("❌ No database found.")
            return {"msg": "No active databases found."}
    except Exception as e:
        logger.info(f"❌ There was an error getting the active databases: {e}")
        return None

    # Get the database status
    try:
        database_status = scrapper.get_database_status(driver, database_name)
        logger.info(f"✅ Database status: {database_status}")
        pass
    except Exception as e:
        logger.info(f"❌ There was an error getting the database status: {e}")
        return None
    finally:
        scrapper.close_browser(driver)
    #if database_status
