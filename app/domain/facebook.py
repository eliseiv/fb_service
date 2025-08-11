from abc import ABC, abstractmethod
from typing import Type, Optional

from selenium.webdriver.chrome.webdriver import WebDriver

from parsel import Selector
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from app.domain.utils.logutils import init_logger
from app.domain.utils.proxy_manager import pmd, pwm
from app.domain.utils.wdm import SeleniumBaseWebDriver
from app.infrastructure.schemas import FacebookItem
from app.infrastructure.settings import LOG_DIR, WDM_PROXY


class FacebookBaseParser:
    def __init__(self, search_type: str = 'business'):
        self.logger = init_logger(filename=f"facebook_{search_type}.log", logdir=str(LOG_DIR))

    def initialize_driver(self, proxy: str = None) -> Optional[WebDriver]:
        try:
            return SeleniumBaseWebDriver.driver_factory(proxy=proxy)
        except Exception as e:
            self.logger.error(f"Error initializing WebDriver: {e}")
            return None

    def fetch_content(self, link: str) -> str:
        result = ''
        try:
            content = self._fetch_with_driver(link)
            if content:
                result = content
        except Exception as err:
            self.logger.error(err)
        return result

    def _verify_cloudflare_captcha(self, selector: Selector) -> bool:
        result = False
        try:
            text = selector.xpath("//head/title/text()").get(default="")
            if "just a moment" in text.strip().lower():
                result = True
        except Exception as err:
            self.logger.error(err)
        return result

    def _fetch_with_driver(self, url: str) -> str | None:
        result = ''
        captcha = False
        driver = None
        for i in range(5):
            if pmd.get_active_proxy_count() < 1 or i == 4:
                proxy_domain = None
                proxy = WDM_PROXY
            else:
                proxy_domain = pmd.get_proxy() or None
                proxy = f'socks5://{proxy_domain}'

            if proxy_domain is None and proxy != WDM_PROXY:
                self.logger.info(f'{proxy}: Bad proxy')
                continue

            try:
                driver = self.initialize_driver(proxy=proxy)
                if not driver:
                    continue
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//html[@id='facebook']")))

                content = driver.page_source
                selector = Selector(text=content)
                captcha = self._verify_cloudflare_captcha(selector)

                if content and not captcha:
                    self.logger.info(f'{proxy} [{i + 1}]: Url - {url} - True')
                    result = content
                elif not content:
                    self.logger.info(f'{proxy} [{i + 1}]: Url - {url} - no content')
                elif captcha:
                    self.logger.info(f"{proxy} [{i + 1}]: Url - {url} - captcha cloudflare")

            except (TimeoutException, Exception):
                self.logger.warning(f'{proxy} [{i + 1}]: Url - {url} - failed to retrieve the page content...')

            finally:
                driver.quit()
                if proxy_domain is not None:
                    if captcha:
                        pmd.set_proxy(proxy_domain, is_bad=True)
                    else:
                        pmd.set_proxy(proxy_domain, is_bad=False)
                if result:
                    break

        return result


class FacebookWeb2Parser:
    def __init__(self, search_type: str = 'business'):
        self.logger = init_logger(filename=f"facebook_{search_type}.log", logdir=str(LOG_DIR))

    def initialize_driver(self, proxy: str = None) -> Optional[WebDriver]:
        try:
            return SeleniumBaseWebDriver.driver_factory(proxy=proxy)
        except Exception as e:
            self.logger.error(f"Error initializing WebDriver: {e}")
            return None

    def fetch_content(self, link: str) -> str:
        result = ''
        try:
            content = self._fetch_with_driver(link)
            if content:
                result = content
        except Exception as err:
            self.logger.error(err)
        return result

    def _verify_cloudflare_captcha(self, selector: Selector) -> bool:
        result = False
        try:
            text = selector.xpath("//head/title/text()").get(default="")
            if "just a moment" in text.strip().lower():
                result = True
        except Exception as err:
            self.logger.error(err)
        return result

    def _check_login_redirect(self, driver: WebDriver, original_url: str) -> bool:
        """
        Проверяет, произошло ли перенаправление на страницу логина
        """
        try:
            current_url = driver.current_url
            if "login" in current_url.lower() or "login" in current_url:
                self.logger.warning(f"Redirected to login page. Original: {original_url}, Current: {current_url}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking login redirect: {e}")
            return False

    def _fetch_with_driver(self, url: str) -> str | None:
        result = ''
        captcha = False
        driver = None

        # Увеличиваем количество попыток до 10: 5 с обычными прокси + 5 с residential
        max_attempts = 3
        regular_proxy_attempts = 1  # Первые 5 попыток с обычными прокси

        # Логируем начальное состояние прокси
        proxy_stats = pwm.get_proxy_stats()
        self.logger.info(f"Starting fetch for {url}. Proxy stats: {proxy_stats}")

        for i in range(max_attempts):
            # Определяем тип прокси для текущей попытки
            if i < regular_proxy_attempts and not pwm.should_use_only_residential():
                # Первые 5 попыток: используем обычные прокси (если не превышен лимит неудач)
                if pwm.get_active_proxy_count() < 1:
                    proxy_domain = None
                    proxy = WDM_PROXY
                    self.logger.info(
                        f"Attempt {i + 1}/{max_attempts}: No regular proxies available, using residential: {proxy}")
                else:
                    proxy_domain = pwm.get_proxy() or None
                    if proxy_domain:
                        proxy = f'socks5://{proxy_domain}'
                        self.logger.info(f"Attempt {i + 1}/{max_attempts}: Using regular proxy: {proxy}")
                    else:
                        proxy = WDM_PROXY
                        proxy_domain = None
                        self.logger.info(
                            f"Attempt {i + 1}/{max_attempts}: No regular proxy available, using residential: {proxy}")
            else:
                # Последние 5 попыток или превышен лимит неудач: используем residential прокси
                proxy_domain = None
                proxy = WDM_PROXY
                if pwm.should_use_only_residential():
                    self.logger.info(f"Attempt {i + 1}/{max_attempts}: Using residential proxy (regular limit exceeded): {proxy}")
                else:
                    self.logger.info(f"Attempt {i + 1}/{max_attempts}: Using residential proxy: {proxy}")

            if proxy_domain is None and proxy != WDM_PROXY:
                self.logger.info(f'{proxy}: Bad proxy')
                continue

            try:
                driver = self.initialize_driver(proxy=proxy)
                if not driver:
                    self.logger.warning(f"Failed to initialize driver with proxy: {proxy}")
                    if proxy_domain:
                        pwm.set_proxy(proxy_domain, is_bad=True)
                        pwm.increment_regular_proxy_failures()  # Увеличиваем счетчик неудач
                        self.logger.info(f"Marked proxy {proxy_domain} as bad due to driver initialization failure")
                    continue

                # Загружаем страницу
                driver.get(url)

                # Ждем загрузки основного HTML
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//html[@id='facebook']")))
                except TimeoutException:
                    self.logger.warning(f"Timeout waiting for Facebook page to load with proxy: {proxy}")
                    if proxy_domain:
                        pwm.set_proxy(proxy_domain, is_bad=True)
                        pwm.increment_regular_proxy_failures()  # Увеличиваем счетчик неудач
                        self.logger.info(f"Marked proxy {proxy_domain} as bad due to page load timeout")
                    continue

                # Проверяем на перенаправление на страницу логина
                login_detected = False
                if self._check_login_redirect(driver, url):
                    self.logger.warning(f'{proxy} [{i + 1}]: Login redirect detected - removing proxy from queue')
                    login_detected = True
                    if proxy_domain:
                        # Сразу удаляем прокси из очереди без возврата
                        pwm.remove_proxy(proxy_domain)
                        pwm.increment_regular_proxy_failures()  # Увеличиваем счетчик неудач
                        self.logger.info(f"Removed proxy {proxy_domain} from queue due to login redirect")
                    continue

                # Ждем загрузки AJAX контента
                import time
                time.sleep(3)  # Ждем 3 секунды для загрузки AJAX

                # Дополнительное ожидание для загрузки AJAX контента
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'xieb3on')]")))
                except TimeoutException:
                    self.logger.info(f"xieb3on elements not found after 20 seconds for {url}")

                    # Диагностика: проверим, что есть на странице
                    try:
                        # Проверим, есть ли вообще div элементы
                        all_divs = driver.find_elements(By.TAG_NAME, "div")
                        self.logger.info(f"Total div elements on page: {len(all_divs)}")

                        # Проверим, есть ли элементы с классом, содержащим 'x'
                        x_elements = driver.find_elements(By.XPATH, "//div[contains(@class,'x')]")
                        self.logger.info(f"Div elements with 'x' in class: {len(x_elements)}")

                        # Проверим title страницы
                        title = driver.title
                        self.logger.info(f"Page title: {title}")

                        # Проверим URL после загрузки
                        current_url = driver.current_url
                        self.logger.info(f"Current URL: {current_url}")

                    except Exception as e:
                        self.logger.error(f"Error during diagnostics: {e}")

                content = driver.page_source
                selector = Selector(text=content)
                captcha = self._verify_cloudflare_captcha(selector)

                if content and not captcha:
                    self.logger.info(f'{proxy} [{i + 1}]: Url - {url} - True')
                    result = content
                    break  # Успешно получили контент
                elif not content:
                    self.logger.info(f'{proxy} [{i + 1}]: Url - {url} - no content')
                elif captcha:
                    self.logger.info(f"{proxy} [{i + 1}]: Url - {url} - captcha cloudflare")

            except (TimeoutException, Exception) as e:
                self.logger.warning(
                    f'{proxy} [{i + 1}]: Url - {url} - failed to retrieve the page content... Error: {e}')
                if proxy_domain:
                    pwm.increment_regular_proxy_failures()  # Увеличиваем счетчик неудач

            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception as e:
                        self.logger.warning(f"Error closing driver: {e}")
                if proxy_domain is not None and not login_detected:
                    if captcha:
                        pwm.set_proxy(proxy_domain, is_bad=True)
                        pwm.increment_regular_proxy_failures()  # Увеличиваем счетчик неудач
                        self.logger.info(f"Marked proxy {proxy_domain} as bad due to captcha")
                    else:
                        pwm.set_proxy(proxy_domain, is_bad=False)

        if not result:
            self.logger.error(f"Failed to fetch content for {url} after {max_attempts} attempts")
            # Логируем финальное состояние прокси
            final_proxy_stats = pwm.get_proxy_stats()
            self.logger.info(f"Final proxy stats after failed attempts: {final_proxy_stats}")

        return result


class Page(ABC):
    @abstractmethod
    def worker(self, item: FacebookItem) -> Optional[FacebookItem]:
        pass

class FacebookPageFactory:
    _registry = {}

    @classmethod
    def register_page(cls, page_type: str, page_class: Type[Page], **kwargs):
        if not issubclass(page_class, Page):
            raise TypeError(f"{page_class} must be a subclass of Page")
        cls._registry[page_type] = page_class

    @classmethod
    def create_page(cls, page_type: str, **kwargs) -> Page:
        page_class = cls._registry.get(page_type)
        if not page_class:
            raise ValueError(f"Unknown page type: {page_type}")
        return page_class(**kwargs)
