from concurrent import futures
from queue import Queue
from typing import List

import httpx
import threading
import logging
from collections import defaultdict

from bounded_pool_executor import BoundedThreadPoolExecutor

from app.domain.utils.logutils import init_logger
from app.infrastructure.settings import WDM_PROXY, LOG_DIR
from app.presentation.grpc_api import GRPC

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = init_logger(filename="facebook.log", logdir=str(LOG_DIR))


class ProxyManager:
    """
    Управление списком прокси-серверов, проверка их доступности и
    предоставление функциональных прокси для использования.
    """
    total_proxy = 0
    max_failures = 5

    def __init__(self, proxies: List[str]):
        """
        Инициализация очереди для хороших и заблокированных прокси,
        словарь для отслеживания ошибок прокси и
        блокировку для синхронизации доступа к ресурсам.
        """
        self.good_proxies = Queue()
        self.failed_proxies = defaultdict(int)
        self.banned_proxies = set()
        self.lock = threading.Lock()
        self.total_proxy = self.good_proxies.qsize()
        self.proxies = proxies

    def import_proxies(self):
        """
        Импортирует прокси из списка, проверяет их доступность и добавляет
        в очередь good_proxies, если они работоспособны.
        """
        with BoundedThreadPoolExecutor(max_workers=50) as executor:
            futures_ = {executor.submit(self._check_proxy, proxy, f'socks5://{proxy}'): proxy for proxy in self.proxies}

            for future in futures.as_completed(futures_):
                proxy = futures_[future]
                try:
                    result = future.result(timeout=5)
                    if result:
                        self.good_proxies.put(proxy)
                except futures.TimeoutError:
                    pass  # Прокси не работает, игнорируем
                except Exception as e:
                    logger.error(f"Ошибка при проверке прокси {proxy}: {e}")


    @staticmethod
    def _check_proxy(proxy, fullproxy=None):
        """
        Проверка работоспособности прокси при запросе к ident.me.
        """
        try:
            response = httpx.get("http://ident.me", proxies={"http://": fullproxy, "https://": fullproxy}, timeout=5)
            return proxy, response.status_code == 200
        except httpx.RequestError:
            return proxy, False

    def get_proxy(self):
        """
        Возвращает рботоспособный прокси из очереди или резиденциальный прокси.
        """
        with self.lock:
            if not self.good_proxies.empty():
                return self.good_proxies.get()
            else:
                return None

    def set_proxy(self, proxy, is_bad=False):
        """
        Управляйте статусом прокси. Если он помечен как нерабочий(is_bad=True), счетчик ошибок увеличивается.
        Если счетчик ошибок превышает лимит, прокси перемещается в очередь banned_proxies.
        В противном случае прокси возвращается в очередь good_proxies.

        Args:
            proxy: URL прокси.
            is_bad (bool): True если прокси нерабочий.
        """
        with self.lock:
            if is_bad and proxy:
                # Помечаем прокси как нерабочий
                self.failed_proxies[proxy] += 1

                # Если прокси нерабочий больше чем лимит, перемещаем его в banned_proxies
                if self.failed_proxies[proxy] >= self.max_failures:
                    self.banned_proxies.add(proxy)
                    return
            else:
                # Сбрасываем счетчик ошибок, если он не помечен как нерабочий
                self.failed_proxies[proxy] = 0

            if proxy not in self.banned_proxies:
                self.good_proxies.put(proxy)

    def get_r_proxy(self):
        """
        Возвращает резидентный прокси если он доступен.
        """
        # return self.residential_proxy
        return f'http://{WDM_PROXY}'

    def get_active_proxy_count(self):
        """
        Return the number of good proxies available.

        Returns:
            int: The number of good proxies available.
        """
        return self.good_proxies.qsize()

    def get_total_proxy_count(self):
        """
        Return the total number of proxies.

        Returns:
            int: The total number of proxies.
        """
        return self.total_proxy

    def get_banned_proxy_count(self):
        """
        Return the number of banned proxies.

        Returns:
            int: The number of banned proxies.
        """
        return len(self.banned_proxies)


class ProxyWebManager:
    """
    Управление списком прокси-серверов, проверка их доступности и
    предоставление функциональных прокси для использования.
    """
    total_proxy = 0
    max_failures = 3  # Уменьшаем количество попыток до 3
    max_regular_proxy_failures = 25  # Максимальное количество неудачных попыток с обычными прокси

    def __init__(self, proxies: List[str]):
        """
        Инициализация очереди для хороших и заблокированных прокси,
        словарь для отслеживания ошибок прокси и
        блокировку для синхронизации доступа к ресурсам.
        """
        self.good_proxies = Queue()
        self.failed_proxies = defaultdict(int)
        self.banned_proxies = set()
        self.lock = threading.Lock()
        self.total_proxy = len(proxies)
        self.proxies = proxies
        self.regular_proxy_failures = 0  # Глобальный счетчик неудачных попыток с обычными прокси
        logger.info(f"Initialized ProxyManager with {self.total_proxy} proxies")

    def import_proxies(self):
        """
        Импортирует прокси из списка, проверяет их доступность и добавляет
        в очередь good_proxies, если они работоспособны.
        """
        logger.info(f"Starting proxy import for {len(self.proxies)} proxies")
        with BoundedThreadPoolExecutor(max_workers=50) as executor:
            futures_ = {executor.submit(self._check_proxy, proxy, f'socks5://{proxy}'): proxy for proxy in self.proxies}

            for future in futures.as_completed(futures_):
                proxy = futures_[future]
                try:
                    result = future.result(timeout=5)
                    if result:
                        self.good_proxies.put(proxy)
                except futures.TimeoutError:
                    logger.warning(f"Proxy {proxy} timed out during check")
                except Exception as e:
                    logger.error(f"Ошибка при проверке прокси {proxy}: {e}")

        logger.info(f"Proxy import completed. Good proxies: {self.good_proxies.qsize()}")


    @staticmethod
    def _check_proxy(proxy, fullproxy=None):
        """
        Проверка работоспособности прокси при запросе к ident.me.
        """
        try:
            response = httpx.get("http://ident.me", proxies={"http://": fullproxy, "https://": fullproxy}, timeout=5)
            return proxy, response.status_code == 200
        except httpx.RequestError:
            return proxy, False

    def get_proxy(self):
        """
        Возвращает рботоспособный прокси из очереди или резиденциальный прокси.
        """
        with self.lock:
            if not self.good_proxies.empty():
                proxy = self.good_proxies.get()
                logger.info(f"Retrieved proxy from queue: {proxy}")
                return proxy
            else:
                logger.warning("No good proxies available in queue")
                return None

    def set_proxy(self, proxy, is_bad=False):
        """
        Управляйте статусом прокси. Если он помечен как нерабочий(is_bad=True), счетчик ошибок увеличивается.
        Если счетчик ошибок превышает лимит, прокси перемещается в очередь banned_proxies.
        В противном случае прокси возвращается в очередь good_proxies.

        Args:
            proxy: URL прокси.
            is_bad (bool): True если прокси нерабочий.
        """
        with self.lock:
            if is_bad and proxy:
                # Помечаем прокси как нерабочий
                self.failed_proxies[proxy] += 1
                logger.warning(f"Proxy {proxy} marked as bad. Failures: {self.failed_proxies[proxy]}/{self.max_failures}")

                # Если прокси нерабочий больше чем лимит, перемещаем его в banned_proxies
                if self.failed_proxies[proxy] >= self.max_failures:
                    self.banned_proxies.add(proxy)
                    logger.error(f"Proxy {proxy} banned after {self.failed_proxies[proxy]} failures")
                    return
            else:
                # Сбрасываем счетчик ошибок, если он не помечен как нерабочий
                if proxy in self.failed_proxies:
                    self.failed_proxies[proxy] = 0
                    logger.info(f"Reset failure count for proxy {proxy}")

            if proxy not in self.banned_proxies:
                self.good_proxies.put(proxy)
                logger.info(f"Returned proxy {proxy} to queue. Queue size: {self.good_proxies.qsize()}")

    def get_r_proxy(self):
        """
        Возвращает резидентный прокси если он доступен.
        """
        # return self.residential_proxy
        return f'http://{WDM_PROXY}'

    def get_active_proxy_count(self):
        """
        Return the number of good proxies available.

        Returns:
            int: The number of good proxies available.
        """
        count = self.good_proxies.qsize()
        logger.debug(f"Active proxy count: {count}")
        return count

    def get_total_proxy_count(self):
        """
        Return the total number of proxies.

        Returns:
            int: The total number of proxies.
        """
        return self.total_proxy

    def get_banned_proxy_count(self):
        """
        Return the number of banned proxies.

        Returns:
            int: The number of banned proxies.
        """
        return len(self.banned_proxies)

    def get_proxy_stats(self):
        """
        Возвращает статистику по прокси
        """
        return {
            'total': self.total_proxy,
            'active': self.good_proxies.qsize(),
            'banned': len(self.banned_proxies),
            'failed': len(self.failed_proxies),
            'regular_failures': self.regular_proxy_failures,
            'max_regular_failures': self.max_regular_proxy_failures
        }

    def should_use_only_residential(self):
        """
        Проверяет, нужно ли использовать только residential прокси
        после превышения лимита неудачных попыток с обычными прокси
        """
        return self.regular_proxy_failures >= self.max_regular_proxy_failures

    def increment_regular_proxy_failures(self):
        """
        Увеличивает счетчик неудачных попыток с обычными прокси
        """
        with self.lock:
            self.regular_proxy_failures += 1
            logger.warning(f"Regular proxy failure #{self.regular_proxy_failures}/{self.max_regular_proxy_failures}")
            
            if self.regular_proxy_failures >= self.max_regular_proxy_failures:
                logger.error(f"Reached maximum regular proxy failures ({self.max_regular_proxy_failures}). Switching to residential only.")

    def remove_proxy(self, proxy):
        """
        Удаляет прокси из очереди без возврата.
        Используется когда прокси привел к логину Facebook.
        
        Args:
            proxy: URL прокси для удаления
        """
        with self.lock:
            # Добавляем в забаненные прокси
            self.banned_proxies.add(proxy)
            logger.info(f"Proxy {proxy} removed from queue and banned due to login redirect")



PROXIES = GRPC.get_proxies()
pmd = ProxyManager(PROXIES)
pmd.import_proxies()

pwm = ProxyWebManager(PROXIES)
pwm.import_proxies()