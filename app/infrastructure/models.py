from datetime import datetime
from django.db import models
from django.db.models import Index
from psqlextra.manager import PostgresManager
from django.utils.translation import gettext_lazy as _
from manage import init_django
from urllib.parse import urlparse
from django.urls import reverse
import hashlib

init_django()

def normalize_url(url):
    result = ""
    try:
        if url and url.strip():
            url = url.replace("https://", "http://")
            tld_parts = urlparse(url.strip().rstrip('/'))
            fqdn = tld_parts.netloc
            schema = tld_parts.scheme
            path = tld_parts.path
            fragment = tld_parts.fragment
            query = tld_parts.query
            if fqdn.startswith('www'):
                fqdn = fqdn.replace('www.', '')

            res = ""
            if schema:
                res += f"{schema}://"
            if fqdn:
                res += f'{fqdn}'
            if path:
                res += f'{path}'
            if query:
                res += f'?{query}'
            if fragment:
                res += f'#{fragment}'
            result = res.rstrip('/')
    except Exception as err:
        pass
    return result


class ParsersSetting(models.Model):
    name = models.CharField(max_length=100, unique=True, primary_key=True)
    value = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Setting")
        verbose_name_plural = _("Settings")
        db_table = "api_parserssetting"

    def __str__(self):
        return f"{self.name}: {self.value}"

class PaymentOrder(models.Model):
    pgsql = PostgresManager()
    objects = models.Manager()

    order_id = models.CharField(max_length=1024, default="", null=False,
                                help_text=_("Order payment transaction unique ID"))
    order_status = models.CharField(max_length=255, default="VOIDED", null=False,
                                    help_text=_("Order status. Must be one of: VOIDED or COMPLITED"))
    payer_name = models.CharField(max_length=1024, default="", help_text=_("Payer first name"))
    payer_surname = models.CharField(max_length=1024, default="", help_text=_("Payer surname"))
    payer_email = models.CharField(max_length=1024, default="", db_index=True, help_text=_("Payer email"))
    purchase_descr = models.TextField(default="", help_text=_("Purchase description."))
    purchase_amount = models.CharField(max_length=19, default="", help_text=_("Purchase amount"))
    purchase_items_quantity = models.IntegerField(default=0, help_text=_("Purchased items quantity"))
    purchase_items_delivered = models.IntegerField(default=0, help_text=_("Number of delivered items"))
    purchase_date = models.DateTimeField(default=datetime.now, help_text=_("Purchase date"))
    delivered_status = models.BooleanField(default=False, help_text=_("Delivering status"))
    keyword = models.JSONField(default=list, help_text=_("Keyword/s used in search api"))
    data_link = models.TextField(default="", help_text=_("API link to access resource"))
    fingerprint = models.CharField(max_length=128, default="", db_index=True, help_text=_("Payer fingerprint"))
    timestamp = models.DateTimeField(auto_now_add=True, help_text=_("Record timestamp"))

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        db_table = "api_paymentorder"

    def __str__(self):
        return f"#{self.order_id}-{self.payer_email}"

class OrderItem(models.Model):
    class SearchModeStatus(models.TextChoices):
        BUSINESS = 'business', _("Business")
        WEB = 'web', _("Web")
        PEOPLE = 'people', _("People")

    pgsql = PostgresManager()
    objects = models.Manager()

    title = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Title"))
    address = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Address"))
    phone = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Phone"))
    email = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Email"))
    keyword = models.CharField(max_length=8184, default="", db_index=True, help_text=_("Keyword"))
    keyword_variant = models.CharField(max_length=8184, default="", db_index=True, help_text=_("Keyword variant from google"))
    place = models.CharField(max_length=4092, default="", help_text=_("Place"))
    web = models.TextField(default="", help_text=_("Website"))
    short_links = models.TextField(default="", help_text=_("Short Links"))
    descr = models.TextField(default="", help_text=_("Description"))
    rating = models.CharField(max_length=22, default="", help_text=_("Rating"))
    review = models.CharField(max_length=22, default="", help_text=_("Review"))
    reviews = models.TextField(default="", help_text=_("Reviews"))
    service = models.CharField(max_length=4092, default="", null=False, help_text=_("Service and price"))
    likes = models.CharField(max_length=4092, default="", null=False, help_text=_("Likes and folowers"))
    social = models.TextField(default="", help_text=_("Social links"))
    groupid = models.IntegerField(default=0, help_text=_("Keyword Group ID"))
    relevance = models.FloatField(default=0.0, db_index=True, help_text=_('Relevance by keyword similarity'))
    rank = models.FloatField(default=0.0, help_text=_('Rank by rank formula'))
    weight = models.IntegerField(default=0, help_text=_("Item weight based on columns filling"))
    source = models.CharField(max_length=1024, default="custom",
                              help_text=_("Source. Must be one of <em>GOOGLE</em> or <em>CUSTOM</em>"))
    parsing_source = models.CharField(max_length=1024, default="custom", help_text=_("Parsing Source."))
    category = models.TextField(default="", help_text=_("Category"))
    builtwith = models.TextField(default="", help_text=_("Builtwith"))
    logo = models.TextField(default="", null=False, help_text=_("Logo url"))
    company_revenue = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Revenue"))
    company_employees = models.PositiveIntegerField(default=0, help_text=_("Employees count"))
    company_founded = models.CharField(max_length=12, default="", help_text=_("Foundation year"))
    main_industry = models.CharField(max_length=4092, default="", help_text=_("Main Industry"))
    company_total_visit = models.CharField(max_length=12, default="", help_text=_("Total Visit"))
    order = models.ForeignKey(PaymentOrder, on_delete=models.CASCADE, related_name="items", verbose_name=_("Order items"))
    crawled_link = models.ForeignKey('CrawlerLink', null=True, blank=True, on_delete=models.SET_NULL, related_name='orderitems', help_text=_("Crawled Link"))
    timestamp = models.DateTimeField(auto_now_add=True, help_text=_("Record timestamp"))
    search_type = models.CharField(max_length=64, choices=SearchModeStatus.choices,
                                   default=SearchModeStatus.BUSINESS, help_text=_("Search request mode: Business, Web or Peoples"))

    synonyms_log = models.TextField(default="", help_text=_("Synonyms log"))
    relevance_log = models.TextField(default="", help_text=_("Relevance log"))
    rank_log = models.TextField(default="", help_text=_("Rank log"))
    keyword_match_log = models.TextField(default="", help_text=_("Keywords match words with text serach log"))
    domain = models.CharField(max_length=1024, default="", db_index=True, help_text=_("Domain name"))
    datanyze_c_link = models.CharField(default="", max_length=4092, db_index=True, help_text=_("Datanyze Company link"))

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        ordering = ['-timestamp']
        db_table = "api_orderitem"

        indexes = [
            Index(name="sf_parsin_source_index", fields=["parsing_source"])
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'web', 'address', 'phone', 'order'],
                name='unique_orderitem_tkwapo',
            )
        ]

    def __str__(self):
        return f"#{self.id}-{self.title}"

class PeopleItem(models.Model):
    pgsql = PostgresManager()
    objects = models.Manager()

    first_name = models.CharField(max_length=4092, default="", db_index=True, help_text=_("First Name"))
    last_name = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Last Name"))
    job_title = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Job Title"))
    position = models.PositiveIntegerField(default=9999999, help_text=_("Position priority in company"))
    company_name = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Company Name"))
    person_link = models.TextField(default="", help_text=_("Person link"))
    phone = models.CharField(max_length=1024, default="", db_index=True, help_text=_("Phone"))
    email = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Email"))
    email_pattern = models.CharField(max_length=500, default="", db_index=True, help_text=_("Email pattern"))
    email_percentage = models.FloatField(default=0.0, help_text=_("Email Percentage"))
    other_email_patterns = models.CharField(max_length=500, default="", db_index=True, help_text=_("Email pattern"))
    address = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Address"))
    web = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Website"))
    revenue = models.CharField(max_length=4092, default="", db_index=True, help_text=_("Revenue"))
    employees_count = models.PositiveIntegerField(default=0, help_text=_("Employees count"))
    founded_year = models.CharField(max_length=12, help_text=_("Foundation year"))
    social = models.TextField(default="", help_text=_("Social links"))
    source_link = models.CharField(default="", max_length=4092, db_index=True, help_text=_("Source link"))
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="peoples", verbose_name=_("Order Item"))
    oid = models.CharField(max_length=1024, default="", null=False, db_index=True, help_text=_("Order payment transaction unique ID"))
    timestamp = models.DateTimeField(auto_now_add=True, help_text=_("Record timestamp"))

    class Meta:
        verbose_name = _("People")
        verbose_name_plural = _("Peoples")
        ordering = ['-timestamp']
        db_table = 'api_peopleitem'

        constraints = [
            models.UniqueConstraint(
                fields=['first_name', 'last_name', 'job_title', 'email', 'web', 'source_link', 'oid'],
                name='peoples_uc',
            )
        ]

    def __str__(self):
        return f"#{self.id}-{self.first_name} {self.last_name}"

class CrawlerLink(models.Model):
    class CrawlingStatus(models.TextChoices):
        INITIAL = 'initial', _("Initial")
        PROCESSED = 'processed', _("Processed")
        REJECTED = 'rejected', _("Rejected")

    class LinkType(models.TextChoices):
        LONG = 'long', _("Long")
        SHORT = 'short', _("Short")

    pgsql = PostgresManager()
    objects = models.Manager()

    oid = models.CharField(max_length=1024, default="", null=False, help_text=_("Order ID"))
    idx = models.IntegerField(default=0, help_text=_("Index Number"))
    link = models.TextField(default="", null=False, help_text=_("Url"))
    hashed = models.CharField(max_length=256, db_index=True, editable=False)
    domain = models.CharField(max_length=8092, default="", db_index=True, help_text=_("Domain"))
    keyword = models.CharField(max_length=8184, default="", db_index=True, help_text=_("Keyword"))
    status = models.CharField(max_length=128, default=CrawlingStatus.INITIAL, choices=CrawlingStatus.choices)
    linktype = models.CharField(max_length=128, default=LinkType.LONG, choices=LinkType.choices)
    kind = models.CharField(max_length=256, default="general")
    depth = models.IntegerField(default=0, help_text=_("Link Depth"))
    pidx = models.IntegerField(default=-1, help_text=_("Parent Index Number"))
    root_pidx = models.IntegerField(default=-1, help_text=_("Root Index Number"))
    root_link = models.TextField(default="", null=False, help_text=_("Root Link"))
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children',
                               help_text=_("Parent UrlItem"))
    timestamp = models.DateTimeField(auto_now_add=True, help_text=_("Timestamp"))

    class Meta:
        db_table = 'api_crawlerlink'
        verbose_name = _("Crawler link")
        verbose_name_plural = _("Crawler links ")
        ordering = ['-timestamp']

        indexes = [
            Index(name='title_crawlerlink_idx', fields=['hashed'], opclasses=['varchar_pattern_ops'])
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['oid', 'keyword', 'idx'],
                name='unique_crawlerhashed_tkwapo',
            )
        ]

    def save(self, *args, **kwargs):
        if not self.hashed:
            self.hashed = hashlib.sha1(str(self.link).encode()).hexdigest()
        if not self.domain:
            self.domain = self.extract_domain(self.link)
        super().save(*args, **kwargs)

    @staticmethod
    def hash_link(url: str):
        result = ""
        try:
            # Using SHA-1 to generate a hash of the long_link
            result = hashlib.sha1(url.encode()).hexdigest()
        except Exception as err:
            pass
        return result

    @staticmethod
    def extract_domain(url):
        result = ""
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                parts = parsed.netloc.split('.')
                if parts:
                    if parts[0] in ('www', 'http', 'https'):
                        result = '.'.join(parts[1:])
                    else:
                        result = '.'.join(parts[0:])
        except Exception as err:
            pass
        return result

    @staticmethod
    def get_linktype(url):
        result = 'short'
        try:
            url_ = normalize_url(url)
            tld_parts = urlparse(url_)
            path = tld_parts.path
            fragment = tld_parts.fragment
            query = tld_parts.query

            if path or query or fragment:
                result = 'long'
        except Exception as err:
            pass
        return result

    def __str__(self):
        return f"#{self.pk}-{self.link}"

    def get_absolute_url(self):
        return reverse('test_crawlerlink_detail', args=[self.pk])
