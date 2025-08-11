import time
from concurrent import futures
from typing import Type, Generator, Any

from bounded_pool_executor import BoundedThreadPoolExecutor
from concurrent import futures

from app.domain.facebook import FacebookPageFactory
from app.domain.facebook_business_page import FacebookBusinessPage
from app.domain.facebook_web_page import FacebookWebPage
from app.domain.utils.logutils import init_logger
from app.domain.utils.tracker import tracker
from app.infrastructure.repositories import RedisRepository, RedisWebRepository, OrderItemRepository
from app.infrastructure.schemas import FacebookItem
from app.infrastructure.settings import LOG_DIR, FACEBOOK_THREADS


class FacebookBusinessService:
    def __init__(self, oid: str, search_type: str, keyword: str):
        self.search_type: str = search_type
        self.oid: str = oid
        self.keyword: str = keyword

        self.parser: Type[FacebookPageFactory] = FacebookPageFactory
        self.page = self.parser.create_page(self.search_type)
        self.repository = OrderItemRepository()
        self.logger = init_logger(filename="facebook_business.log", logdir=str(LOG_DIR))
        self.logger.info(f'=================== START PROCESS Facebook {self.search_type.upper()} SERVICE =================')
        self.logger.info(f'oid={oid} | search_type={search_type}')

    def process(self) -> int:
        updated_amount = 0
        try:
            items = self.repository.get_items(oid=self.oid)

            self.logger.info(f"Imported {len(items)} items.")
            for chunk in self.chunks_generator(items, FACEBOOK_THREADS):
                result = []
                with BoundedThreadPoolExecutor(FACEBOOK_THREADS) as executor:
                    futures_list = [
                        executor.submit(self.__worker, item)
                        for item in chunk
                    ]

                    for finished in futures.as_completed(futures_list):
                        if finished.result() is not None:
                            result.append(finished.result())

                saved = self.repository.save_items(oid=self.oid, items=result)
                updated_amount += saved
                self.logger.info(f"{saved} items updated in 1 chunk.")

        except Exception as e:
            self.logger.error(f"Error in process: {e}")

        self.logger.info(f"Final DB: {updated_amount} items updated!")
        self.logger.info(f'================ END PROCESS Facebook {self.search_type.upper()} SERVICE ================')
        return updated_amount

    def __worker(self, item: FacebookItem) -> FacebookItem:
        result = item
        try:
            result = self.page.worker(item)
        except Exception as e:
            self.logger.error(e)

        return result

    @staticmethod
    def chunks_generator(data: list[Any], size: int) -> Generator[list[Any], None, None]:
        for i in range(0, len(data), size):
            yield data[i:i + size]


class FacebookGoogleService:
    def __init__(self, oid: str, search_type: str):
        self.search_type: str = search_type
        self.oid: str = oid

        self.parser: Type[FacebookPageFactory] = FacebookPageFactory
        self.page = self.parser.create_page(self.search_type)
        self.repository = RedisRepository()
        self.logger = init_logger(filename="facebook_google.log", logdir=str(LOG_DIR))
        self.logger.info(f'=================== START PROCESS Facebook {self.search_type.upper()} SERVICE =================')
        self.logger.info(f'oid={oid} | search_type={search_type}')

    def process(self) -> int:
        updated_amount = 0
        psd_processed = False
        while not psd_processed:
            try:
                psd_processed = self.repository.check_psd_processed(self.oid)
                items = self.repository.get_items(self.oid)
                if not items:
                    time.sleep(1)
                    continue

                self.logger.info(f"Imported {len(items)} items.")
                for chunk in self.chunks_generator(items, FACEBOOK_THREADS):
                    result = []
                    with BoundedThreadPoolExecutor(FACEBOOK_THREADS) as executor:
                        futures_list = [
                            executor.submit(self.__worker, item)
                            for item in chunk
                        ]

                        for finished in futures.as_completed(futures_list):
                            if finished.result() is not None:
                                result.append(finished.result())

                    saved = self.repository.save_items(self.oid, result)
                    updated_amount += saved
                    self.logger.info(f"{saved} items updated in 1 chunk.")

            except Exception as e:
                self.logger.error(f"Error in process: {e}")

        self.repository.clean_redis_key(self.oid)
        self.repository.batch_insert(self.oid)
        self.logger.info(f"Final DB: {updated_amount} items updated!")
        self.logger.info(f'================ END PROCESS Facebook {self.search_type.upper()} SERVICE ================')
        return updated_amount

    def __worker(self, item: FacebookItem) -> FacebookItem:
        result = item
        try:
            result = self.page.worker(item)
        except Exception as e:
            self.logger.error(e)

        return result

    @staticmethod
    def chunks_generator(data: list[Any], size: int) -> Generator[list[Any], None, None]:
        for i in range(0, len(data), size):
            yield data[i:i + size]


class FacebookWebService:
    def __init__(self, oid: str, search_type: str):
        self.search_type: str = search_type
        self.oid: str = oid

        self.parser: Type[FacebookPageFactory] = FacebookPageFactory
        self.page = self.parser.create_page(self.search_type)
        self.repository = RedisWebRepository()
        self.logger = init_logger(filename="facebook_web.log", logdir=str(LOG_DIR))
        self.logger.info(f'=================== START PROCESS Facebook {self.search_type.upper()} SERVICE =================')
        self.logger.info(f'oid={oid} | search_type={search_type}')

    def __del__(self):
        self.logger.info(f'================ END PROCESS Facebook {self.search_type.upper()} SERVICE ================')

    def process(self) -> int:
        updated_amount = 0
        waited = 0
        max_wait = 300 # 5 minutes
        while waited < max_wait:
            try:
                items = self.repository.get_items(self.oid)
                if not items:
                    waited += 1
                    time.sleep(1)
                    continue

                waited = 0
                max_wait = 1 # Lower wait time after getting first items
                self.logger.info(f"Imported {len(items)} items.")
                result: list[Any] = []
                with futures.ThreadPoolExecutor(max_workers=FACEBOOK_THREADS) as executor:
                    future_to_item = {
                        executor.submit(self.__worker, item): item
                        for item in items
                    }
                    for future in futures.as_completed(future_to_item):
                        res = future.result()
                        if res is not None:
                            result.append(res)

                saved = self.repository.save_items(self.oid, result)
                updated_amount += saved
                self.logger.info(f"{saved} items updated in this batch.")

            except Exception as e:
                self.logger.error(f"Error in process: {e}")
        else:
            self.logger.info(f"No new items for {max_wait}s. Quitting process.")

        # self.repository.clean_redis_key(self.oid)
        self.repository.batch_insert(self.oid)
        
        # Очищаем трекер после завершения обработки
        tracker.clear()
        
        self.logger.info(f"Final DB: {updated_amount} items updated!")
        return updated_amount

    def __worker(self, item: FacebookItem) -> FacebookItem:
        result = item
        try:
            result = self.page.worker(item)
        except Exception as e:
            self.logger.error(e)

        return result

    @staticmethod
    def chunks_generator(data: list[Any], size: int) -> Generator[list[Any], None, None]:
        for i in range(0, len(data), size):
            yield data[i:i + size]


FacebookPageFactory.register_page("business", FacebookBusinessPage)
FacebookPageFactory.register_page("web", FacebookWebPage)
FacebookPageFactory.register_page("google", FacebookBusinessPage)


if __name__ == "__main__":
    facebook = FacebookGoogleService(
        oid="ch_3RmbsJGefNSPz2RI1KGVbkNp",
        search_type="business"
    )
    facebook.process()