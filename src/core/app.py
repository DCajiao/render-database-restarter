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
