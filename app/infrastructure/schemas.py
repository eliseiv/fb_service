from pydantic import BaseModel


class FacebookItem(BaseModel):
    id: int = 0
    logo: str = ''
    address: str = ''
    phone: str = ''
    email: str = ''
    web: str = ''
    service: str = ''
    descr: str = ''
    description: str = ''
    rating: str = ''
    category: str = ''
    likes: str = ''
    title: str = ''
    price_range: str = ''
    price_delivery: str = ''
    social: str = ''
    keyword: str = ''
    builtwith: str = ''
    keyword_match_log: str = ''
    relevance_log: str = ''
    search_type: str = ''
    relevance: float = 0.0
    position: int = 0
    order_id: int = 0
