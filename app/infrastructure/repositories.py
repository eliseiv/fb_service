import redis
import json

from django.db import connections

from app.domain.utils.logutils import init_logger
from app.domain.utils.tracker import tracker
from app.infrastructure.models import PaymentOrder, OrderItem
from app.infrastructure.schemas import FacebookItem
from app.infrastructure.settings import LOG_DIR, REDIS_HOST, REDIS_PORT, REDIS_PASS


logger = init_logger(filename="facebook.log", logdir=str(LOG_DIR))


class RedisRepository:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS)
        self.r4 = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS, db=4)
        self.r15 = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS, db=15)

    def get_items(self, key: str) -> list[FacebookItem]:
        result = []
        try:
            if not self.r4.exists(key):
                return []

            items = self.r4.lrange(key, 0, -1)
            decode_items = [json.loads(i.decode()) for i in items]
            result = [
                FacebookItem(
                    **item
                )
                for item in decode_items
                if not tracker.processed(item.get('web',''))
            ]
        except Exception as e:
            logger.error(f"Error retrieving data from Redis: {e}")
        return result

    def save_items(self, key: str, items: list[FacebookItem]):
        try:
            existing_raw = self.r.lrange(key, 0, -1)
            existing = []

            # Normalize existing entries: replace 'link' with 'web' if needed
            for item in existing_raw:
                loaded = json.loads(item)
                if 'link' in loaded and 'web' not in loaded:
                    loaded['web'] = loaded.pop('link')
                existing.append(loaded)

            # Build mapping from 'web'
            existing_map = {e['web']: e for e in existing}

            # Prepare updated items
            added = []
            for item in items:
                tracker.add(item)
                dumped = item.model_dump()
                if dumped['web'] in existing_map:
                    existing_map[dumped['web']] = dumped
                    added.append(dumped)

            self.r.delete(key)
            self.r.rpush(key, *(json.dumps(e) for e in existing_map.values()))

            return len(added)

        except (redis.RedisError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error saving items to Redis: {e}")
            return 0

    def clean_redis_key(self, key: str) -> None:
        try:
            if self.r4.exists(key):
                self.r4.delete(key)
            else:
                logger.warning(f"Redis key '{key}' does not exist.")

            if self.r15.exists(key):
                self.r15.delete(key)
        except redis.RedisError as e:
            logger.error(f"Error cleaning Redis key '{key}': {e}")

    def batch_insert(self, key: str) -> int:
        """
        Add all the items in the tracker to the Redis database.
        This is done because some of the items may have been skipped
        in save_items due to non-matching 'web' keys. So we
        ensure that all items in the tracker are saved to Redis.
        """
        items = tracker.get()
        serialized_items = [
            json.dumps(item.model_dump(exclude_unset=True))
            for item in items
        ]

        if serialized_items:
            self.r.delete(key)
            self.r.rpush(key, *serialized_items)
            self.r.expire(key, 60 * 60 * 24 * 7)

        return len(serialized_items)

    def check_psd_processed(self, key: str) -> bool:
        try:
            if not self.r15.exists(key):
                return False

            if self.r15.get(key) == b'3':
                return True

            return False
        except Exception as e:
            logger.error(f"Error checking Google processed: {e}")
            return False


class RedisWebRepository:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS, db=0)

    def get_items(self, key: str) -> list[FacebookItem]:
        result = []
        try:
            if not self.r.exists(key):
                return []

            items = self.r.lrange(key, 0, -1)
            decode_items = [json.loads(i.decode()) for i in items]

            for item in decode_items:
                if not tracker.processed(item.get('web', '')):
                    result.append(FacebookItem(**item))

        except Exception as e:
            logger.error(f"Error retrieving data from Redis: {e}")
        return result

    def save_items(self, key: str, items: list[FacebookItem]):
        try:
            existing_raw = self.r.lrange(key, 0, -1)
            existing_items = []

            for item in existing_raw:
                loaded = json.loads(item)
                if 'link' in loaded and 'web' not in loaded:
                    loaded['web'] = loaded.pop('link')

                existing_items.append(loaded)

            existing_map = {e['web']: e for e in existing_items}

            updated_count = 0
            for item in items:
                tracker.add(item)
                dumped = item.model_dump()

                if dumped['web'] in existing_map:
                    # Обновляем только непустые поля, сохраняя существующие данные
                    existing_item = existing_map[dumped['web']]
                    for field, value in dumped.items():
                        if value and field != 'web':  # Не перезаписываем web и пустые значения
                            existing_item[field] = value
                        # ВАЖНО: Если поле пустое в результате facebook_service, но было заполнено в исходных данных - сохраняем исходное
                        elif not value and field in existing_item and existing_item[field] and field != 'web':
                            # Сохраняем исходное значение, если facebook_service не смог заполнить поле
                            pass  # Оставляем исходное значение
                    updated_count += 1

            final_items = []

            for original_item in existing_items:
                web_key = original_item.get('web', '')

                if web_key in existing_map:
                    final_items.append(existing_map[web_key])
                else:
                    final_items.append(original_item)

            if final_items:
                self.r.delete(key)
                self.r.rpush(key, *(json.dumps(e) for e in final_items))
                self.r.expire(key, 60 * 60 * 24 * 7)  # 7 дней
                logger.info(f"Saved {len(final_items)} items to Redis key: {key}")

            return updated_count

        except (redis.RedisError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error saving items to Redis: {e}")
            return 0

    def clean_redis_key(self, key: str) -> None:
        try:
            if self.r.exists(key):
                self.r.delete(key)
                logger.info(f"Cleaned Redis key: {key}")
            else:
                logger.warning(f"Redis key '{key}' does not exist.")
        except redis.RedisError as e:
            logger.error(f"Error cleaning Redis key '{key}': {e}")

    def batch_insert(self, key: str) -> int:
        items = tracker.get()

        if not items:
            logger.info("No items in tracker to batch insert")
            return 0

        try:
            existing_raw = self.r.lrange(key, 0, -1)
            existing_items = []

            for item in existing_raw:
                loaded = json.loads(item)
                if 'link' in loaded and 'web' not in loaded:
                    loaded['web'] = loaded.pop('link')


                existing_items.append(loaded)

            existing_map = {e.get('web', ''): e for e in existing_items}

            updated_count = 0
            for item in items:
                dumped = item.model_dump(exclude_unset=True)

                if dumped.get('web') in existing_map:
                    # Обновляем только непустые поля, сохраняя существующие данные
                    existing_item = existing_map[dumped['web']]
                    for field, value in dumped.items():
                        if value and field != 'web':  # Не перезаписываем web и пустые значения
                            existing_item[field] = value
                        # ВАЖНО: Если поле пустое в результате facebook_service, но было заполнено в исходных данных - сохраняем исходное
                        elif not value and field in existing_item and existing_item[field] and field != 'web':
                            # Сохраняем исходное значение, если facebook_service не смог заполнить поле
                            pass  # Оставляем исходное значение
                    updated_count += 1

            final_items = []

            for original_item in existing_items:
                web_key = original_item.get('web', '')

                if web_key in existing_map:
                    final_items.append(existing_map[web_key])
                else:
                    final_items.append(original_item)

            if final_items:
                self.r.delete(key)
                self.r.rpush(key, *(json.dumps(e) for e in final_items))
                self.r.expire(key, 60 * 60 * 24 * 7)
                logger.info(f"Batch inserted {updated_count} items, total {len(final_items)} items in Redis key: {key}")

            return updated_count

        except Exception as e:
            logger.error(f"Error in batch_insert: {e}")
            return 0


class OrderItemRepository:

    @staticmethod
    def get_items(oid: str) -> list:
        result = []
        try:
            order = PaymentOrder.objects.filter(order_id__exact=oid).first()
            if not order:
                logger.error(f"Order with oid {oid} not found.")
                return result

            qs = OrderItem.objects.filter(order_id=order.id)
            result = [
                FacebookItem(
                    id=item.id,
                    logo=item.logo,
                    address=item.address,
                    phone=item.phone,
                    email=item.email,
                    web=item.web,
                    service=item.service,
                    descr=item.descr,
                    rating=item.rating,
                    category=item.category,
                    likes=item.likes,
                    title=item.title,
                    social=item.social,
                    keyword=item.keyword,
                    builtwith=item.builtwith,
                    keyword_match_log=item.keyword_match_log,
                    relevance_log=item.relevance_log,
                    search_type=item.search_type,
                    relevance=item.relevance,
                    order_id=order.id,
                )
                for item in qs
                if 'facebook.com' in item.social
            ]
        except Exception as e:
            logger.error(f"Error retrieving items for order {oid}: {e}")
        return result

    @staticmethod
    def save_items(oid: str, items: list[FacebookItem]) -> int:
        fields = [
            'logo', 'address', 'phone', 'email', 'web', 'service',
            'descr', 'rating', 'category', 'likes',
            'title', 'social', 'keyword', 'builtwith', 'keyword_match_log',
            'relevance_log', 'search_type', 'relevance'
        ]
        num_updated = 0
        try:
            order = PaymentOrder.objects.filter(order_id__exact=oid).first()
            existing_keys = {
                (o.title, o.web, o.address, o.phone, o.order_id): o.id
                for o in OrderItem.objects.filter(order_id=order.id)
            }

            instances = []
            for item in items:
                if not item.id:
                    continue

                new_key = (item.title, item.web, item.address, item.phone, order.id)

                if new_key in existing_keys and existing_keys[new_key] != item.id:
                    logger.warning(f"Skipping update due to duplicate key conflict for item ID={item.id}")
                    continue

                instances.append(
                    OrderItem(
                        id=item.id,
                        logo=item.logo,
                        address=item.address,
                        phone=item.phone,
                        email=item.email,
                        web=item.web,
                        service=item.service,
                        descr=item.descr,
                        rating=item.rating,
                        category=item.category,
                        likes=item.likes,
                        title=item.title,
                        social=item.social,
                        keyword=item.keyword,
                        builtwith=item.builtwith,
                        keyword_match_log=item.keyword_match_log,
                        relevance_log=item.relevance_log,
                        search_type=item.search_type,
                        relevance=item.relevance,
                        order_id=order.id,
                    )
                )

            if instances:
                num_updated = OrderItem.objects.bulk_update(instances, fields, batch_size=50)

        except Exception as err:
            logger.error(f"Error occurred during saving: {err}")
        finally:
            connections['default'].close()

        return num_updated
