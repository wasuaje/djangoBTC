"""btc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
import app.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', app.views.main, name='main'),
    url(r'^transaction/$', app.views.index_transaction),
    url(r'^transaction/add/$', app.views.add_transaction),
    url(r'^transaction/edit/(?P<pk>\d+)$', app.views.edit_transaction),
    url(r'^transaction/delete/(?P<pk>\d+)$', app.views.delete_transaction),
    url(r'^transaction/bulkload/$', app.views.bulkload_transaction),
    url(r'^transaction/bulkload/confirm/$', app.views.bulkload_transaction_confirm),
    url(r'^stats/$', app.views.index_stats),
    url(r'^test/$', app.views.test_kraken),
]
