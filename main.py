import asyncio
from app.infrastructure.settings import LOG_DIR
from app.domain.utils.logutils import init_logger
from app.presentation.broker import RabbitMQBroker
import argparse

logger = init_logger(filename="facebook.log", logdir=str(LOG_DIR))

async def main():
    try:
        parser = argparse.ArgumentParser(
            prog='FacebookParsing',
            description='App to parse data from facebook.com/...'
        )
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-b', '--business',
                            help='Consume data from business query',
                            action='store_true')
        group.add_argument('-w', '--web',
                           help='Consume data from web query',
                           action='store_true')
        group.add_argument('-g', '--google',
                           help='Consume data from web query',
                           action='store_true')

        args, unknown = parser.parse_known_args()

        search_type = 'business'
        if args.business:
            search_type = 'business'
        elif args.web:
            search_type = 'web'
        elif args.google:
            search_type = 'google'
        else:
            logger.error("Search type is not declared: business")

        logger.info(f"STARTING Facebook {search_type.upper()}")
        async with RabbitMQBroker(search_type=search_type, env_settings=True) as broker:
            await broker.consume_from_izpaysite()
    except Exception as err:
        logger.error(f"Error: {err}")

if __name__ == '__main__':
    asyncio.run(main())
