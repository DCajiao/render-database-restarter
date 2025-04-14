# -*- coding: utf-8 -*-
# This file contains the main application logic for the web scraping tool.

import logging

import core.scrapper as scrapper
import utils.definitions as definitions


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
    
    # database_status -> {'deployed_at': '2025-04-13T18:23:40.452102Z', 'hours_used': 10.35, 'hours_left': 739.65, 'percentage_used': 1.38, 'estimated_expiration': '2025-05-15 00:23:40 UTC', 'storage_used_percent': 0.048}
    
    # Check if the database is near expiration
    hours_left = database_status['hours_left']
    percentage_used = database_status['percentage_used']
    
    if hours_left > definitions.DB_HOURS_LEFT_THRESHOLD or percentage_used < 0.5:
        # Database is not near expiration
        msg = f"✅ Database is running fine. Hours left: {hours_left}. Percentage used: {percentage_used}."
        logger.info(msg)
        return {"msg": msg}
    
    elif hours_left <= definitions.DB_HOURS_LEFT_THRESHOLD and percentage_used >= 0.5:
        # Database is near expiration
        msg = f"⚠️ Database is near expiration. Hours left: {hours_left}. Percentage used: {percentage_used}."
        logger.info(msg)
        return {"msg": msg}
