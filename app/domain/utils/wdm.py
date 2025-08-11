import sys
import psutil

from seleniumbase import Driver

from app.domain.utils.logutils import init_logger
from app.infrastructure.settings import LOG_DIR

sys.argv.append("-n")
logger = init_logger(filename="facebook.log", logdir=str(LOG_DIR))

class WebDriverFactory:
    @staticmethod
    def get_common_options(proxy: str = None, cache_path: str = None):
        arguments = [
            "--disable-gpu",
            "--disable-notifications",
            "--disable-infobars",
            "--disable-setuid-sandbox",
            "--allow-running-insecure-content",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-site-isolation-trials",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank"
        ]

        if proxy:
            arguments.append(f"--proxy-server={proxy}")
        if cache_path:
            arguments.append(f"--cache-path={cache_path}")

        return arguments

    @staticmethod
    def kill_browsers():
        chrome_names = [
            'chrome',
            'cat',
            'chrome_crashpad',
            'undetected_chro',
            'chrome_crashpad_handler',
            'chromedriver',
            'uc_driver'
        ]
        for proc in psutil.process_iter():
            try:
                proc_name = proc.name()

                if proc_name and any(proc_name.endswith(name) for name in chrome_names):
                    proc.terminate()
                    proc.wait(timeout=1)
            except Exception:
                pass


class SeleniumBaseWebDriver(WebDriverFactory):
    @staticmethod
    def driver_factory(proxy: str = None):
        try:
            options_list = WebDriverFactory.get_common_options(proxy)
            driver = Driver(headless=False, uc=True, proxy=proxy)

            for arg in options_list:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": f"window.chrome = {arg}"})

            return driver
        except Exception as err:
            logger.error(f"Error in SeleniumBaseWebDriver: {err}")
            return None
