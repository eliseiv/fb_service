import time
import json, aio_pika, asyncio
from typing import Optional, Tuple

from app.domain.utils.logutils import init_logger
from app.infrastructure.settings import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_DEFAULT_USER, RABBITMQ_DEFAULT_PASS, LOG_DIR

from aio_pika.abc import AbstractRobustConnection, AbstractIncomingMessage
from aio_pika import ExchangeType, Message
from asgiref.sync import sync_to_async
from app.applications.services import FacebookGoogleService, FacebookWebService, FacebookBusinessService

logger = init_logger(filename="facebook.log", logdir=str(LOG_DIR))


class RabbitMQBroker:
    def __init__(
        self,
        search_type: str = 'business',
        host='localhost',
        port=5672,
        login='guest',
        password='guest',
        env_settings: bool = False,
    ):
        if env_settings:
            self.host = RABBITMQ_HOST
            self.port = RABBITMQ_PORT
            self.login = RABBITMQ_DEFAULT_USER
            self.password = RABBITMQ_DEFAULT_PASS
        else:
            self.host = host
            self.port = port
            self.login = login
            self.password = password
        self.search_type = search_type
        self.connection: Optional[AbstractRobustConnection] = None

    async def __aenter__(self):
        self.connection = await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            await self.connection.close()

    async def connect(self) -> Optional[AbstractRobustConnection]:
        connection = None
        try:
            connection =  await aio_pika.connect_robust(
                f"amqp://{self.login}:{self.password}@{self.host}:{self.port}/",
            )
        except Exception as err:
            logger.error(err)
        return connection

    async def consume_from_izpaysite(self):
        exchange_name = 'send_to_facebook_ex'
        queue_name = 'send_to_facebook_b_q'
        routing_key = 'facebook_b'

        try:
            if self.search_type == 'business':
                queue_name = 'send_to_facebook_b_q'
                routing_key = 'facebook_b'

            elif self.search_type == 'web':
                queue_name = 'send_to_facebook_w_q'
                routing_key = 'facebook_w'

            elif self.search_type == 'google':
                queue_name = 'send_to_facebook_g_q'
                routing_key = 'facebook_g'

            async with self.connection.channel() as channel:
                await channel.declare_exchange(exchange_name, durable=True, type=ExchangeType.DIRECT)
                await channel.set_qos(prefetch_count=1)
                queue = await channel.declare_queue(queue_name, durable=True)
                await queue.bind(exchange=exchange_name, routing_key=routing_key)

                await queue.consume(self.__on_message)
                logger.info("Waiting messages from izpaysite...")
                await asyncio.Future()
        except Exception as err:
            logger.error(err)

    async def publish_to_izpaysite(self, oid: str, updated_amount: int):
        exchange_name = 'ack_from_facebook_ex'
        routing_key = f"ack_facebook_{oid}"
        try:
            async with self.connection.channel() as channel:
                exchange = await channel.declare_exchange(exchange_name, durable=False, type=ExchangeType.DIRECT)

                message_body = json.dumps({
                    'oid': oid,
                    'updated_amount': updated_amount,
                }).encode('utf-8')

                message = Message(body=message_body)
                time.sleep(5)
                await exchange.publish(message, routing_key=routing_key)
        except Exception as err:
            logger.error(err)

    async def __on_message(self, message: AbstractIncomingMessage):
        try:
            async with message.process(ignore_processed=True):
                new_message = message.body
                new_message = json.loads(new_message.decode('utf-8'))
                oid = new_message['oid']
                keyword = new_message.get('keyword', None)
                updated_amount = await self.process(oid, keyword=keyword)

                await message.ack()
                await self.publish_to_izpaysite(oid, updated_amount)
        except Exception as err:
            logger.error(err)

    async def process(self, oid: str, keyword: str = None) -> int:
        updated_amount = 0
        try:
            if self.search_type == 'business':
                updated_amount = await sync_to_async(
                    FacebookBusinessService(
                        oid=oid, search_type=self.search_type, keyword=keyword
                    ).process)()
            elif self.search_type == 'web':
                updated_amount = await sync_to_async(
                    FacebookWebService(
                        oid=oid, search_type=self.search_type
                    ).process)()
            elif self.search_type == 'google':
                updated_amount = await sync_to_async(
                    FacebookGoogleService(
                        oid=oid, search_type=self.search_type
                    ).process)()
        except Exception as err:
            logger.error(err)
        return updated_amount
