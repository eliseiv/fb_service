import regex as re
from typing import Optional
from urllib.parse import unquote

from parsel import Selector

from app.domain.facebook import Page, FacebookBaseParser, FacebookWeb2Parser
from app.domain.utils.logutils import init_logger
from app.infrastructure.schemas import FacebookItem
from app.infrastructure.settings import LOG_DIR

logger = init_logger(filename="facebook_web.log", logdir=str(LOG_DIR))


class FacebookWebParser:
    @staticmethod
    def __parse_likes_intro(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '(//div[@role="main"])[1]//a[contains(@href, "_like")]//text()')
            text = " ".join([e.get().strip() for e in elems])
            text = re.sub(r'like[s]?', '', text)
            result = text.strip()
        except Exception as err:
            logger.error(err)

        return result

    @staticmethod
    def __parse_likes_about(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//i[@data-visualcompletion="css-img" and contains(@style, "-168px -105px")]'
                '/parent::div/following-sibling::div//text()'
            )
            text = " ".join([e.get().strip() for e in elems])
            text = re.sub(r'\b\s+(people|person)\s+like[s]?\s+this\b', '', text)
            result = text.strip()
        except Exception as err:
            logger.error(err)

        return result

    @staticmethod
    def __parse_followers_intro(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath('(//div[@role="main"])[1]//a[contains(@href, "follower")]//text()')
            text = " ".join([e.get().strip() for e in elems])
            text = re.sub(r'follower[s]?', '', text)
            result = text.strip()
        except Exception as err:
            logger.error(err)

        return result

    @staticmethod
    def __parse_followers_about(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//i[@data-visualcompletion="css-img" and contains(@style, "0px -176px")]'
                '/parent::div/following-sibling::div//text()'
            )
            text = " ".join([e.get().strip() for e in elems])
            text = re.sub(r'\b\s+(people|person)\s+follow[s]?\s+this\b', '', text)
            result = text.strip()
        except Exception as err:
            logger.error(err)

        return result

    @staticmethod
    def __parse_email_intro(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//img[contains(@src,"2PIcyqpptfD.png")]/parent::div/following-sibling::div//text()')
            text = " ".join([e.get().strip() for e in elems])
            result = text.strip()
        except Exception as err:
            logger.error(err)

        return result

    @staticmethod
    def __parse_email_about(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//i[@data-visualcompletion="css-img" and contains(@style, "0px -155px")]'
                '/parent::div/following-sibling::div//text()')
            text = " ".join([e.get().strip() for e in elems])
            result = text.strip()
        except Exception as err:
            logger.error(err)

        return result

    @staticmethod
    def __parse_phone_intro(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//img[contains(@src,"Dc7-7AgwkwS.png")]/parent::div/following-sibling::div//text()')
            text = " ".join([e.get().strip() for e in elems])
            result = text.strip()
        except Exception as err:
            logger.error(err)
        return result

    @staticmethod
    def __parse_phone_about(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//i[@data-visualcompletion="css-img" and contains(@style, "-63px -126px")]'
                '/parent::div/following-sibling::div//text()'
            )
            text = " ".join([e.get().strip() for e in elems])
            result = text.strip()
        except Exception as err:
            logger.error(err)
        return result

    @staticmethod
    def __parse_web_intro(selector: Selector) -> str:
        result = ""
        pattern = re.compile(r'\?u\=((.+))&', re.IGNORECASE)
        try:
            text = selector.xpath(
                '//img[contains(@src,"BQdeC67wT9z.png")]/parent::div/following-sibling::div//a/@href').get()

            if not text:
                return result

            found = pattern.search(text.strip())
            if found:
                und = found[1]
                result = unquote(und)
        except Exception as e:
            logger.error(e)

        return result

    @staticmethod
    def __parse_web_about(selector: Selector) -> str:
        result = ""
        pattern = re.compile(r'\?u\=((.+))&', re.IGNORECASE)
        try:
            text = selector.xpath(
                '//i[@data-visualcompletion="css-img" and contains(@style, "0px -260px")]'
                '/parent::div/following-sibling::div//text()'
            ).get()

            if not text:
                return result

            found = pattern.search(text.strip())
            if found:
                und = found[1]
                result = unquote(und)
        except Exception as err:
            logger.error(err)
        return result

    @staticmethod
    def __parse_address_intro(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//img[contains(@src,"8k_Y-oVxbuU.png")]/parent::div/following-sibling::div//text()')
            text = " ".join([e.get().strip() for e in elems])
            result = text.strip()
        except Exception as err:
            logger.error(err)
        return result

    @staticmethod
    def __parse_address_about(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//i[@data-visualcompletion="css-img" and contains(@style, "-84px -126px")]'
                '/parent::div/following-sibling::div//text()'
            )
            text = " ".join([e.get().strip() for e in elems])
            result = text.strip()
        except Exception as err:
            logger.error(err)
        return result

    @staticmethod
    def __parse_price_range_intro(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//img[contains(@src,"vUmfhJXfJ5R.png")]/parent::div/following-sibling::div//text()')
            text = " ".join([e.get().strip() for e in elems])
            matches = re.findall(r'\$+', text, flags=re.I)
            result = matches[0].strip() if len(matches) > 0 else ""
        except Exception as e:
            logger.error(e)

        return result

    @staticmethod
    def __parse_price_range_about(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//i[@data-visualcompletion="css-img" and contains(@style, "0px -134px")]'
                '/parent::div/following-sibling::div//text()'
            )
            text = " ".join([e.get().strip() for e in elems])
            matches = re.findall(r'\$+', text, flags=re.I)
            result = matches[0].strip() if len(matches) > 0 else ""
        except Exception as err:
            logger.error(err)
        return result

    @staticmethod
    def __parse_category_intro(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//img[contains(@src,"4PEEs7qlhJk.png")]/parent::div/following-sibling::div//text()'
            )
            text = " ".join([e.get().strip() for e in elems])
            result = text.replace('Page ·', '').strip()
        except Exception as e:
            logger.error(e)

        return result

    @staticmethod
    def __parse_category_about(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//i[@data-visualcompletion="css-img" and contains(@style, "0px -42px")]'
                '/parent::div/following-sibling::div//text()'
            )
            text = " ".join([e.get().strip() for e in elems])
            result = text.strip()
        except Exception as err:
            logger.error(err)
        return result

    # PARSE METHODS
    def parse_likes(self, selector: Selector) -> str:
        result = ""
        try:
            result = self.__parse_likes_intro(selector)
            if not result:
                result = self.__parse_likes_about(selector)
        except Exception as e:
            logger.error(e)

        return result

    def parse_followers(self, selector: Selector) -> str:
        result = ""
        try:
            result = self.__parse_followers_intro(selector)
            if not result:
                result = self.__parse_followers_about(selector)
        except Exception as e:
            logger.error(e)

        return result

    def parse_likes_followers(self, selector: Selector) -> str:
        result = ""
        try:
            likes_ = self.parse_likes(selector)
            followers_ = self.parse_followers(selector)
            result = likes_
            if followers_.strip():
                result += f"/{followers_}"
        except Exception as e:
            logger.error(e)

        return result

    def parse_email(self, selector: Selector) -> str:
        result = ""
        try:
            result = self.__parse_email_intro(selector)
            if not result:
                result = self.__parse_email_about(selector)
        except Exception as e:
            logger.error(e)

        return result

    def parse_phone(self, selector: Selector) -> str:
        result = ""
        try:
            result = self.__parse_phone_intro(selector)
            if not result.strip():
                result = self.__parse_phone_about(selector)
        except Exception as err:
            logger.error(err)
        return result

    def parse_web(self, selector: Selector) -> str:
        result = ""
        try:
            result = self.__parse_web_intro(selector)
            if not result:
                result = self.__parse_web_about(selector)
        except Exception as e:
            logger.error(e)

        return result

    def parse_address(self, selector: Selector) -> str:
        result = ""
        try:
            result = self.__parse_address_intro(selector)
            if not result:
                result = self.__parse_address_about(selector)
        except Exception as e:
            logger.error(e)

        return result

    def parse_price_range(self, selector: Selector) -> str:
        result = ""
        try:
            result = self.__parse_price_range_intro(selector)
            if not result:
                result = self.__parse_price_range_about(selector)
        except Exception as e:
            logger.error(e)

        return result

    def parse_category(self, selector: Selector) -> str:
        result = ""
        try:
            result = self.__parse_category_intro(selector)
            if not result:
                result = self.__parse_category_about(selector)
        except Exception as e:
            logger.error(e)

        return result

    @staticmethod
    def parse_title(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath('(//h1)[1]//text()')
            text = " ".join([e.get().strip() for e in elems])
            result = text.strip()
        except Exception as err:
            logger.error(err)

        return result

    def parse_price_delivery(self, selector: Selector) -> str:
        result = ""
        try:
            price = self.parse_price_range(selector)
            delivery = self.parse_service(selector)
            result = price.strip()
            if delivery.strip():
                result += f'/{delivery}'
        except Exception as e:
            logger.error(e)

        return result

    @staticmethod
    def parse_rating(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath('.//img[contains(@src,"4Lea07Woawi.png")]/parent::div/following-sibling::div//text()')
            text = " ".join([e.get().strip() for e in elems])
            text = text.replace(",", "")
            parts = re.findall(r'\d+\.?\d*', text, flags=re.I)
            rating_ = parts[0].strip() if len(parts) > 0 else ""
            if '0' == rating_.strip() or '0.0' == rating_.strip():
                rating_ = ""
            review_ = parts[1].strip() if len(parts) > 1 else ""
            if '0' == rating_.strip():
                rating_ = ""
            if rating_ and review_:
                result = f"{rating_}/{review_}"
            elif rating_:
                result = rating_
            elif review_:
                result = review_
        except Exception as e:
            logger.error(e)

        return result

    @staticmethod
    def parse_descr(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//div[contains(@class,"xieb3on")]/div[1]//text()')

            if not elems:
                elems = selector.xpath(
                    '//div[contains(@class,"xdppsyt")]//text()')

            if elems:
                text = " ".join([e.get().strip() for e in elems])
                result = text.strip()
        except Exception as e:
            logger.error(f"Error parsing description: {e}")

        return result

    # def parse_descr(selector: Selector) -> str:
    #     result = ""
    #     try:
    #         # Новый селектор - ищем span с описанием в первом div xieb3on
    #         elems = selector.xpath(
    #             '//div[contains(@class,"xieb3on")]/div[1]//span[contains(@class,"x193iq5w") and @dir="auto"]/text()')
    #
    #         if not elems:
    #             # Старый селектор 1
    #             elems = selector.xpath(
    #                 '//div[contains(@class,"xieb3on")]/div[1]//text()')
    #
    #         if not elems:
    #             # Новый селектор - ищем span с описанием
    #             elems = selector.xpath(
    #                 '//div[contains(@class,"xieb3on")]//span[contains(@class,"x193iq5w")]/text()')
    #
    #         if not elems:
    #             # Новый селектор - ищем span с dir="auto"
    #             elems = selector.xpath(
    #                 '//div[contains(@class,"xieb3on")]//span[@dir="auto"]/text()')
    #
    #         if not elems:
    #             elems = selector.xpath(
    #                 '//div[contains(@class,"xieb3on")]//text()')
    #
    #         if not elems:
    #             elems = selector.xpath(
    #                 '//div[contains(@class,"xdppsyt")]//text()')
    #
    #         if elems:
    #             text = " ".join([e.get().strip() for e in elems])
    #             result = text.strip()
    #             if result:
    #                 logger.info(f"Found description: '{result[:100]}...'")
    #         else:
    #             logger.info("No description elements found with current selectors")
    #     except Exception as e:
    #         logger.error(f"Error parsing description: {e}")
    #
    #     return result

    @staticmethod
    def parse_service(selector: Selector) -> str:
        result = ""
        try:
            elems = selector.xpath(
                '//img[contains(@src,"arM1m3sNXPr.png")]/parent::div/following-sibling::div//text()'
            )
            text = " ".join([e.get().strip() for e in elems])
            result = text.strip()
        except Exception as e:
            logger.error(e)

        return result

    @staticmethod
    def parse_logo(selector: Selector) -> str:
        link = ""
        try:
            # Находим первый элемент image внутри svg
            image_elements = selector.xpath("(//svg//image)[1]")

            # Проверяем, что элемент найден
            if image_elements:
                image_element = image_elements[0]
                # Проверяем, что атрибут xlink:href существует
                if 'xlink:href' in image_element.attrib:
                    link = image_element.attrib['xlink:href']
                else:
                    logger.debug("Element found but 'xlink:href' attribute is missing")
            else:
                logger.debug("No SVG image elements found")
        except Exception as e:
            logger.error(f"Error parsing logo: {e}")
        return link


class FacebookWebPage(Page, FacebookWebParser, FacebookWeb2Parser):
    def __init__(self):
        super().__init__(search_type='business')
        self.required_fields = ['logo', 'address', 'phone', 'email', 'title']

    def worker(self, item: FacebookItem) -> FacebookItem:
        result = item
        try:
            urls = self.extract_facebook_urls(item)
            for web in urls:
                content = self.fetch_content(web)
                if content:
                    result = self.extract_item(content, item)
                if self.is_complete(result):  # Проверяем result, а не item
                    break
        except Exception as err:
            logger.error(err)
        return result

    def extract_facebook_urls(self, item: FacebookItem) -> list[str]:
        social_links = [social.strip() for social in item.social.split(' | ')]

        if any("facebook.com" in link for link in social_links or []):
            return [link for link in social_links if "facebook.com" in link]
        return []

    def is_complete(self, item: FacebookItem) -> bool:
        """
        Check if the item has all required fields filled.
        :param item: FacebookItem to check.
        :return: True if all required fields are filled, False otherwise.
        """
        return all(getattr(item, field) for field in self.required_fields)

    def _should_update_description(self, original_desc: str, new_desc: str) -> bool:
        """
        Определяет, нужно ли обновлять поле description.

        Обновляем если:
        1. Исходное описание пустое И новое описание не пустое
        2. Исходное описание содержит '...' в начале или середине И новое описание не пустое

        НЕ обновляем если:
        1. Исходное описание не пустое и не содержит '...'
        2. '...' присутствует только в конце
        3. Новое описание пустое

        :param original_desc: Исходное описание
        :param new_desc: Новое описание из Facebook
        :return: True если нужно обновить, False если оставить исходное
        """
        # Если новое описание пустое - НЕ обновляем
        if not new_desc or new_desc.strip() == '':
            return False
        
        # Если исходное описание пустое - обновляем
        if not original_desc or original_desc.strip() == '':
            return True
        
        # Если исходное описание не содержит '...' - НЕ обновляем
        if '...' not in original_desc:
            return False
        
        # Проверяем, где находится '...'
        dots_index = original_desc.find('...')
        
        # Если '...' в конце - НЕ обновляем
        if dots_index == len(original_desc) - 3:
            return False
        
        # Если '...' в начале или середине - обновляем
        return True

    def extract_item(self, content: str, item: FacebookItem) -> Optional[FacebookItem]:
        try:
            selector = Selector(text=content)

            # Создаем новый объект с данными из парсинга
            parsed_description = self.parse_descr(selector)
            
            parsed_data = {
                'keyword': item.keyword,  # Сохраняем исходный keyword
                'title': self.parse_title(selector),
                'description': parsed_description,
                'web': item.web,  # СОХРАНЯЕМ ИСХОДНЫЙ web, НЕ ИЗМЕНЯЕМ!
                'phone': self.parse_phone(selector),
                'email': self.parse_email(selector),
                'logo': self.parse_logo(selector),
                'address': self.parse_address(selector),
                'service': '',
                'rating': '',
                'category': '',
                'likes': '',
                'price_range': '',
                'price_delivery': '',
                'social': item.social,  # Сохраняем исходный social
                'builtwith': item.builtwith,  # Сохраняем исходный builtwith
                'keyword_match_log': '',
                'relevance_log': '',
                'search_type': '',
                'relevance': 0
            }
            
            result = FacebookItem(**parsed_data)

            # Логика обновления: обновляем только пустые поля
            for field in item.model_fields:
                item_value = getattr(item, field)
                result_value = getattr(result, field)

                # Специальная обработка для поля description
                if field == 'description':
                    if self._should_update_description(item_value, result_value):
                        setattr(result, field, result_value)
                        logger.info(f"Facebook found description: '{result_value}'")
                    else:
                        setattr(result, field, item_value)
                # Для остальных полей - стандартная логика
                else:
                    # Если исходное поле пустое, а новое значение есть - используем новое
                    if not item_value and result_value:
                        setattr(result, field, result_value)
                    # Если исходное поле не пустое - сохраняем исходное
                    elif item_value:
                        setattr(result, field, item_value)
                    # ВАЖНО: Если исходное поле не пустое, а новое пустое - сохраняем исходное
                    elif item_value and not result_value:
                        setattr(result, field, item_value)

            return result

        except Exception as err:
            logger.error(err)
            return None


if __name__ == "__main__":
    # Example usage
    p = FacebookWebPage()
    i = FacebookItem(
        social="https://www.facebook.com/pages/Kims-BBQ-Restaurant/121801967878515",
        keyword="example"
    )
    r = p.worker(i)
    print(r)