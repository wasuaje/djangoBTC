# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
import requests

import datetime
from decimal import Decimal

from safedelete import safedelete_mixin_factory, SOFT_DELETE, \
    DELETED_VISIBLE_BY_PK, safedelete_manager_factory, DELETED_INVISIBLE

TRANSACTION_TYPE_CHOICES = (
    ('B', 'BUY'),
    ('S', 'SELL'),
)


class TimeStampedModel(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


SoftDeleteMixin = safedelete_mixin_factory(policy=SOFT_DELETE,
                                           visibility=DELETED_VISIBLE_BY_PK)


class Platform(TimeStampedModel):
    name = models.CharField(max_length=100)
    accounting_endpoint = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)


class LastImportedId(TimeStampedModel):
    id_numeric = models.IntegerField()
    id_string = models.CharField(max_length=20)
    platform = models.ForeignKey(Platform, default=None)


class SoftDeletableModel(SoftDeleteMixin):
    disabled = models.BooleanField(default=False)
    active_objects = safedelete_manager_factory(models.Manager,
                                                models.QuerySet,
                                                DELETED_INVISIBLE)()

    class Meta:
        abstract = True


class CurrencyManager(models.Manager):

    def get_by_natural_key(self, code):
        return self.get(code=code)


class Currency(TimeStampedModel, SoftDeletableModel):
    objects = CurrencyManager()
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    k_code = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.code


class LocationManager(models.Manager):

    def get_by_natural_key(self, code):
        return self.get(code=code)


class Location(TimeStampedModel, SoftDeletableModel):
    objects = LocationManager()
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.code


class TraderManager(models.Manager):

    def get_by_natural_key(self, code):
        return self.get(code=code)


class Trader(TimeStampedModel, SoftDeletableModel):
    objects = TraderManager()
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.code


class ResourceManager(models.Manager):

    def get_by_natural_key(self, name):
        return self.get(name=name)


class Resource(TimeStampedModel, SoftDeletableModel):
    objects = ResourceManager()
    name = models.CharField(max_length=100)
    location = models.ForeignKey(Location)
    transfer_fee = models.DecimalField(max_digits=5, decimal_places=2,
                                       default="0.00")
    available_currencies = models.ManyToManyField(Currency)
    trader = models.ForeignKey(Trader)  # fi better way

    def __str__(self):
        return self.name

    def natural_key(self):
        return self.name


class Balance(TimeStampedModel, SoftDeletableModel):
    currency = models.ForeignKey(Currency)
    trader = models.ForeignKey(Trader)
    resource = models.ForeignKey(Resource)
    # Going to be rich...
    amount = models.DecimalField(decimal_places=2,
                                 max_digits=15)
    is_initial = models.BooleanField(default=False)


class Transaction(TimeStampedModel, SoftDeletableModel):
    """
    then the profit is (for sell) (sell_price - kraken_price) * amount_of_btc
    buy (kraken_price -  buy_price) * amount_of_btc

    """
    date = models.DateTimeField(default=datetime.datetime.now)
    type = models.CharField(max_length=1, choices=TRANSACTION_TYPE_CHOICES)
    currency_from = models.ForeignKey(Currency, related_name='c_from')
    currency_to = models.ForeignKey(Currency, related_name='c_to')
    amount = models.DecimalField(max_digits=10, decimal_places=2,
                                 default="0.00")
    total = models.DecimalField(max_digits=10, decimal_places=2,
                                default="0.00")
    rate = models.DecimalField(max_digits=10, decimal_places=2, default="0.00")
    override_fee_percent = models.DecimalField(max_digits=5, decimal_places=2,
                                               default="0.00")
    override_fee_sum = models.DecimalField(max_digits=10, decimal_places=2,
                                           default="0.00")
    resource_from = models.ForeignKey(Resource, related_name='r_from')
    resource_to = models.ForeignKey(Resource, related_name='r_to', null=True)
    kraken_price = models.DecimalField(max_digits=10, decimal_places=2,
                                       default="0.00")
    profit = models.DecimalField(max_digits=10, decimal_places=2,
                                 default="0.00")
    trader = models.ForeignKey(Trader, default=1)  # find a better way
    paid = models.BooleanField(default=False)    # trader not needed here
    provisional = models.BooleanField(default=True)
    bulk_loaded = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        ordering = ['-date']

    def OLD_get_last_trade_price(self):
        """
        Receive the currency to trade with BTC
        Receive also the trasaction type B or S to compare
        TODO;
          SET kraken api url as a setting in case it changes
        """

        try:
            url = 'https://api.kraken.com/0/public/Trades?pair=%s%s' % (
                self.currency_from.k_code, self.currency_to.k_code)
            req = requests.get(url)
            data = req.json()
        except:
            return Decimal(0.00)

        try:
            result = data["result"]['%s%s' % (self.currency_from.k_code,
                                              self.currency_to.k_code)]
        except KeyError as e:
            print("Key {} doesn't exist ".format(e))
        else:

            for rs in result:
                if rs[3].upper() == self.type:
                    return rs[0]

    def get_last_trade_price(self):
        """
        Receive the currency to trade with BTC
        Receive also the trasaction type B or S to compare
        TODO;
          SET kraken api url as a setting in case it changes
        """
        rtn = Decimal(0.00)
        try:
            url = 'https://cex.io/api/trade_history/%s/%s/' % (
                self.currency_from.code, self.currency_to.code)
            req = requests.get(url)
            data = req.json()
        except:
            print("==> Error getting data from cex.io")

        else:
            # try:
            #     result = data["result"]['%s%s' % (self.currency_from.k_code,
            #                                       self.currency_to.k_code)]
            # except KeyError as e:
            #     print("Key {} doesn't exist ".format(e))
            # else:

            for rs in data:
                if rs["type"][:1].upper() == self.type:
                    # print "####", rs["price"]
                    rtn = rs["price"]

        return rtn

    def save(self, *args, **kwargs):
        # print self.rate, type(self.rate)
        if not self.bulk_loaded:
            try:
                self.kraken_price = Decimal(self.get_last_trade_price())
            except TypeError as e:
                print("==>", e)
                self.kraken_price = Decimal(0.00)

        if self.rate == "0.00" and self.kraken_price > 0:  # rate is comming with model default value
            self.rate = self.kraken_price

        self.total = self.rate * self.amount

        # Profit when buying
        if Decimal(self.kraken_price) > 0:
            if self.type == 'B':
                self.profit = (Decimal(self.kraken_price)
                               * self.amount) - self.total
        # Profit when selling
            elif self.type == 'S':
                self.profit = Decimal(self.total) - (Decimal(self.kraken_price)
                                                     * self.amount)
        else:
            self.profit = Decimal(0.00)

        # finally the save
        super(Transaction, self).save()
