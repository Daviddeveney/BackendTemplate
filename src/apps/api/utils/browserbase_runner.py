import os
from typing import Dict
from dotenv import load_dotenv
from playwright.sync_api import Playwright, sync_playwright
from browserbase import Browserbase
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

load_dotenv()

BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

bb = Browserbase(api_key=BROWSERBASE_API_KEY)


def run_browserbase(request=None) -> Dict[str, str]:
    """
    Run the browserbase script and return the results.
    
    Args:
        request: Optional HTTP request object containing additional parameters
        
    Returns:
        Dict containing session_url and status
    """
    session = None
    result = {"status": "error", "error": "Unknown error occurred"}
    
    try:
        # Create session with minimal timeout since we're just testing
        session = bb.sessions.create(
            project_id=BROWSERBASE_PROJECT_ID,
            keep_alive=False,
            timeout=60  # Minimum allowed timeout
        )
        session_url = f"https://browserbase.com/sessions/{session.id}"
        
        with sync_playwright() as playwright:
            try:
                # Connect to the remote session with timeout
                chromium = playwright.chromium
                browser = chromium.connect_over_cdp(
                    session.connect_url,
                    timeout=5000  # 5 second connection timeout
                )
                context = browser.contexts[0]
                page = context.pages[0]

                # For testing, we'll just verify we can access the page object
                result = {
                    "status": "success",
                    "session_url": session_url,
                    "page_title": "Test Session"
                }
            except Exception as e:
                logger.error(f"Error in Playwright operations: {str(e)}")
                result = {
                    "status": "error",
                    "error": str(e)
                }
            finally:
                # Clean up Playwright resources within the context
                try:
                    if 'page' in locals():
                        page.close()
                    if 'browser' in locals():
                        browser.close()
                except Exception as cleanup_error:
                    logger.error(f"Error during Playwright cleanup: {str(cleanup_error)}")
                    
    except Exception as e:
        logger.error(f"Error in session creation: {str(e)}")
        result = {
            "status": "error",
            "error": str(e)
        }
    finally:
        # Handle session cleanup outside of Playwright context
        if session and session.keep_alive:
            try:
                bb.sessions.update(
                    session.id,
                    status="REQUEST_RELEASE",
                    project_id=BROWSERBASE_PROJECT_ID
                )
                logger.info(f"Successfully released session {session.id}")
            except Exception as e:
                logger.error(f"Failed to release session {session.id}: {str(e)}")
    
    return result 