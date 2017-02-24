# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Avg, Sum, Count, F
from django.template.loader import get_template
from decimal import Decimal
import csv
import os

import dateutil.parser

from .forms import *
# Create your views here.
# login_required(login_url ='/login/')


def main(request):
    # alido si la empresa esta creada,  debe estarlo
    template = get_template('app/index.html')

    messages = []

    return HttpResponse(template.render({'messages': messages}, request))


def index_transaction(request):
    form_class = DateSearchForm
    model = Transaction
    template = get_template('index_transaction.html')
    paginate_by = 10
    form = form_class(request.POST or None)

    if form.is_valid():
        my_date = form.cleaned_data['date']
        if my_date:
            transaction_list = model.objects.filter(date__date=my_date)
        else:
            transaction_list = model.objects.all()
    else:
        transaction_list = model.objects.all()
    # print transaction_list.query
    # print len(transaction_list)
    # Show 10 rows per page
    paginator = Paginator(transaction_list, paginate_by)
    page = request.GET.get('page')

    try:
        transactions = paginator.page(page)

    except PageNotAnInteger:
        transactions = paginator.page(1)

    except EmptyPage:
        transactions = paginator.page(paginator.num_pages)
    # print transactions.object_list
    return HttpResponse(template.render({'form': form,
                                         'transactions': transactions,
                                         'action': 'Transaction Main'
                                         },
                                        request))


def add_transaction(request):
    messages = []
    template = get_template('transaction.html')
    if request.method == 'POST':
        form = ManageTransaction(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.append('Succesfully saved !')
            # If the save was successful,  redirect to another page

            return HttpResponseRedirect('/transaction/')
    else:
        form = ManageTransaction()

    return HttpResponse(template.render({'form': form,

                                         'action': 'Add'},
                                        request))


def edit_transaction(request, pk):
    messages = []
    transaction = get_object_or_404(Transaction, pk=pk)
    template = get_template('transaction.html')

    form = ManageTransaction(instance=transaction)

    # print form.nombres
    if request.POST:
        form = ManageTransaction(request.POST,
                                 request.FILES, instance=transaction
                                 )

        if form.is_valid():
            form.save()
            # ersona = form.save()
            # his is where you might choose to do stuff.
            # ontact.name = 'test'
            # ersona.save()
            messages.append('Succesfully edited !')
            return HttpResponseRedirect('/transaction/')

    return HttpResponse(template.render({'form': form,

                                         'id': pk,

                                         'action': 'Edit'},
                                        request))


def delete_transaction(request, pk):
    messages = []
    transaction = get_object_or_404(Transaction, pk=pk)
    template = get_template('transaction.html')

    form = ManageTransaction(instance=transaction)

    # print form.nombres
    if request.POST:
        form = ManageTransaction(request.POST,
                                 request.FILES,
                                 instance=transaction)

        if form.is_valid():
            transaction.delete()

            messages.append('Succesfully deleted')
            return HttpResponseRedirect('/transaction/')

    return HttpResponse(template.render({'form': form,
                                         'id': pk,
                                         'action': 'Delete'
                                         },
                                        request))


def bulkload_transaction(request):
    """
    View that shows a upload butto to pick a csv file for later processes
    The file is first stored in /tmp due to django only keeps in memory
    2.5 mb of any file uploaded,  so if file is bigger must behave weird
    I save the file in chunks to make the process more eficient
    """
    messages = []
    template = get_template('bulkload_transaction.html')
    template_confirm = get_template('bulkload_transaction_confirm.html')
    data = {}
    error = ""
    success = ""
    table = ""

    if request.method == 'POST':
        form = ManageBulkloadTransaction(request.POST, request.FILES)
        frm_resource = ResourcePickForm()

        if form.is_valid():
            uploaded_file = request.FILES['csvfile']
            delimiter = request.POST.get('delimiter', ';')
            first_head = request.POST.get('first_head')
            headers = ""
            body = ""

            # Write the file to disk django only keep 2.5MB of files in memory
            # and processes in chunks for performance

            fout = open("/tmp/%s" % uploaded_file.name, 'wb')
            for chunk in uploaded_file.chunks():
                fout.write(chunk)

            # close first to be sure is correctly closed and saved
            fout.close()
            # open again to extract lines and other data
            fh = open("/tmp/%s" % uploaded_file.name)

            # get the data lists
            data = [row for row in csv.reader(fh.read().splitlines(),
                                              delimiter=str(delimiter)
                                              )]
            fh.close()

            success = 'Succesfully parsed, please complete and confirm !'
            start_line = 0 if first_head is None else 1

            input_str = """<td> <input  type ="checkbox" name ="check_exclude"
                            value ="%s" CHECKED> </td>"""
            ini_table = """<table class ="table table-hover

                            table-condensed">"""
            table = ini_table
            # form or picking fields

            FIELD_CHOICES = (
                ('N', '----'),
                ('date', 'Date'),
                ('type', 'Type'),
                ('currency_to', 'Currency'),
                ('amount', 'Total Crypto'),
                ('total', 'Total Fiat'),
                ('rate', 'Rate'),
                ('override_fee_percent', 'Fee Percent'),
                ('override_fee_sum', 'Fee Fiat')
            )

            slt = """<select name ="col_%s">"""
            for ch in FIELD_CHOICES:
                slt += """<option value ="%s">%s</option>""" % (ch[0], ch[1])

            slt += """</select>"""
            # print slt
            # let build the headers
            if first_head:               # f first line of csv is a header
                headers += " <tr> "
                for i in range(0, len(data[0])):

                    frm = slt % i

                    headers += " <th> %s %s </th> " % (data[0][i], frm)
                headers += " <th>  Included </th> "
                headers += " </tr> "
            table += headers
            # lets build data lines
            body += "<tr>"

            for ln in range(start_line, len(data) - 1):
                for rc in data[ln]:
                    body += "<td> %s </td>" % rc
                body += input_str % "row_%s" % ln

                body += "</tr>"
            table += body
            table += "</table>"
            # Input hidden file to send the filename to confirm in order to
            # finally processit and isert data in tables
            table += """<input id ="filename" name ="filename"
                    type ="hidden" value ="%s" >""" % uploaded_file.name
            # Input hidden file to send the delimiter selected in order to
            # finally pass it to the next stage
            table += """<input id ="delimiter" name ="delimiter"
                    type ="hidden" value ="%s" >""" % delimiter

            return HttpResponse(
                template_confirm.render({'form': form,
                                         'frm_resource': frm_resource,
                                         'action': 'Bulk Load Confirm',
                                         'success': success,
                                         'error': error,
                                         'table': table,
                                         'filename': uploaded_file.name},
                                        request))
        else:
            # print form.__dict__["_errors"]
            error = form.__dict__["_errors"]
            return HttpResponse(
                template_confirm.render({'form': form,
                                         'action': 'Bulk Load Confirm',
                                         'success': success,
                                         'error': error,
                                         'table': table
                                         },
                                        request))

    else:

        form = ManageBulkloadTransaction()

    return HttpResponse(template.render({'form': form,

                                         'action': 'Bulk Load'},
                                        request))


def bulkload_transaction_confirm(request):
    """
    Once loaded and data recognizable,  process gets here to finally
    add to DB previuos filtering correct destinations/currencies code etc
    """
    messages = []
    errors = []
    template = get_template('bulkload_transaction_confirm.html')
    data = {}
    error = ""
    success = ""
    # print request
    if request.method == 'POST':
        uploaded_file = request.POST.get('filename')
        delimiter = request.POST.get('delimiter', ',')
        resource = request.POST.get('resource', None)
        included = request.POST.getlist("check_exclude")
        currency_from = request.POST.get('currency_from', None)
        # print request.POST
        # Need a dict with cols to easily match col with model record
        # print "rows",included
        col_dict = {}
        for i in request.POST:
            if "col_" in i and request.POST.get(i) != "N":
                col_dict[i.replace("col_", "")] = request.POST[i]

        # print col_dict
        # Open the file to finally process it
        fh = open("/tmp/%s" % uploaded_file)
        data = [row for row in csv.reader(fh.read().splitlines(),
                                          delimiter=str(delimiter))]
        fh.close()

        all_records_to_add = []
        # print len(included)
        if resource and included:
            for rw in included:     # iterate over selected rows
                line = data[int(str(rw).replace("row_", ""))]
                row_to_add = {}

                for cl in col_dict.keys():  # iter over cols matched
                    new_value, error = _sanitize_record(col_dict[cl],

                                                        line[int(cl)])
                    if error:
                        errors.append(error)
                    else:
                        row_to_add[col_dict[cl]] = new_value

                all_records_to_add.append(row_to_add)

            # resource object instance
            resource_object = Resource.objects.get(pk=resource)
            currency_from_object = Currency.objects.get(pk=currency_from)

            # Add common data to every record
            # print len(all_records_to_add)
            for rc in all_records_to_add:
                rc["resource_from"] = resource_object
                rc["bulk_loaded"] = True
                rc["currency_from"] = currency_from_object
                # print rc

            # get the kraken price given the current list of records
            # to be added to DB
            new_list = _get_kraken_prices_new(all_records_to_add)

            # insert them
            for rc in new_list:
                Transaction.objects.create(**rc)

            # need to group currency pairs to make few queries to kraken
            #
            messages.append("File successfully processed!")

            # remember to remove the file after all
            os.remove("/tmp/%s" % uploaded_file)

        else:
            messages.append("Check for resource or/and included rows")

    return HttpResponse(template.render({'errors': error,
                                         'success': messages
                                         },
                                        request))


def _get_kraken_prices(transactions):
    transaction_list = transactions
    set_pairs = set()
    data = {}

    # Set with unique pairs of currences
    for line in transaction_list:
        # print line
        set_pairs.add(line["currency_from"].k_code +
                      line["currency_to"].k_code)
    # print set_pairs
    # build base dict with uniq set as keys and empyt B and S
    for dt in set_pairs:
        data[dt] = {'B': 0.00, 'S': 0.00}

    # print data
    # only query kraken for the uniq pairs found in data
    for rc in data.keys():
        url = 'https://api.kraken.com/0/public/Trades?pair=%s' % (rc)
        req = requests.get(url)
        res = req.json()

        try:
            # get the list of buy and sell for this only pais
            result = res["result"]['%s' % rc]
            # print result

            for rs in result:
                # get lastest data only for buy if not already set
                if rs[3].upper() == 'B' and data[rc]["B"] == 0:
                    # print "BUY", rc, rs[0]
                    data[rc]["B"] = rs[0]

                # get lastest data only for sell uf not already set
                if rs[3].upper() == 'S' and data[rc]["S"] == 0:
                    # print "SELL", rc, rs[0]
                    data[rc]["S"] = rs[0]

                # if i have both B and S exit loop to save time
                if data[rc]["B"] > 0 and data[rc]["S"] > 0:
                    break
        except:
            pass
        # print data

    # update record list passed with values from kraken where found
    for rec in transaction_list:
        rec["kraken_price"] = data[rec["currency_from"].k_code +
                                   rec["currency_to"].k_code][rec["type"]]

        # rec.save()

    return transaction_list


def test_kraken(request):
    pass


def _get_kraken_prices_new(transactions):
    import datetime
    transaction_list = transactions
    set_pairs = set()
    data = {}

    # print data
    # only query kraken for the uniq pairs found in data
    for rc in transaction_list:
        url = 'https://cex.io/api/trade_history/%s/%s/?since=1' % (
            rc["currency_from"].code, rc["currency_to"].code)

        # check only once for each pair of currencies
        pair = "%s%s" % (rc["currency_from"].code, rc["currency_to"].code)
        if pair in data:
            result = data[pair]
        else:
            req = requests.get(url)
            result = req.json()
            data[pair] = result
        # print rc["currency_from"].code, rc["currency_to"].code, len(result)
        # print result
        # print "DATE1",datetime.datetime.date(rc["date"]).strftime('%Y-%m-%d')

        try:
            # get the list of buy and sell for this only pais
            for rs in result:
                # get lastest data only for buy if not already set
                # print "DATE2",rs["date"]
                # print float(rs["date"])
                # print
                # datetime.datetime.fromtimestamp(int(rs["date"])).strftime('%Y-%m-%d')
                if rs["type"].upper() == 'BUY' and datetime.datetime.date(rc["date"]).strftime(
                        '%Y-%m-%d') == datetime.datetime.fromtimestamp(int(rs["date"])).strftime('%Y-%m-%d'):
                    # print "BUY", rs["price"]
                    rc["kraken_price"] = rs["price"]
                    break
                # get lastest data only for sell uf not already set
                if rs["type"].upper() == 'SELL' and datetime.datetime.date(rc["date"]).strftime(
                        '%Y-%m-%d') == datetime.datetime.fromtimestamp(int(rs["date"])).strftime('%Y-%m-%d'):
                    # print "SELL", rs["price"]
                    rc["kraken_price"] = rs["price"]
                    break
                    # if i have both B and S exit loop to save time
                    # if data[rc]["B"] > 0 and data[rc]["S"] > 0:
                    # break
            # print data
        except:
            pass
    # print "2nd round"

    # last pass trough the data and the results to check for blank
    # done in reverse order from last dato to current to be sure
    # of pickng latestes date
    for rc in transaction_list:
        pair = "%s%s" % (rc["currency_from"].code, rc["currency_to"].code)

        result = data[pair]
        # print result
        # print type(result)
        if isinstance(result, list):
            for rs in reversed(result):
                # print rc
                if rs["type"].upper() == 'BUY' and "kraken_price" not in rc:
                    print("BUY, {}".format(rs["price"]))
                    rc["kraken_price"] = rs["price"]
                    break
                    # get lastest data only for sell uf not already set
                if rs["type"].upper() == 'SELL' and "kraken_price" not in rc:
                    print("SELL".format(rs["price"]))
                    rc["kraken_price"] = rs["price"]
                    break

    # update record list passed with values from kraken where found
    # for rec in transaction_list:
    #    rec["kraken_price"] = data[rec["currency_from"].k_code +
    #                            rec["currency_to"].k_code][rec["type"]]

        # rec.save()

    # checking the success proportion
    # sm1=0
    # sm2=0
    # for i in transaction_list:
    #     if i.kraken_price > 0:
    #         sm1+=1
    #     elif  i.kraken_price == 0:
    #         sm2+=1
    # print sm1,sm2
    return transaction_list


def _sanitize_record(column, value):
    """
    Method to standarize and sanitize column with its datatype.
    Receives the column name and the value to check
    date = datetime
    currency = Currency(code)
    type  = value BUY or SELL upper or lower to return just B or S
    amount = no commas in decimals only dot, decimal value
    total = no commas in decimals only dot, decimal value
    fee_pct = no commas in decimals only dot, decimal value
    fee_sum = no commas in decimals only dot, decimal value
    rate = no commas in decimals only dot, decimal value
    returns new_value and a error message or None
    """

    err_message = None
    decimal_columns_list = ["amount", "total", "override_fee_percent",
                            "override_fee_sum", "rate"]

    if column == "date":
        try:
            new_value = dateutil.parser.parse(value)
        except ValueError as e:
            err_message = "I/O error({0}): {1}".format(e.errno, e.strerror)
            new_value = None

    elif "currency" in column:
        try:
            new_value = Currency.objects.get(code=value)
        except Currency.DoesNotExist as e:
            # err_message = "I/O error({0}): {1}".format(e.errno, e.strerror)
            new_value = Currency.objects.create(code=value, name=value)

    elif column == "type":
        if "BUY" in str(value).upper():
            new_value = 'B'

        if "SELL" in str(value).upper():
            new_value = 'S'

    elif column in decimal_columns_list:
        new_value = Decimal(str(value).replace(",", "."))

    return new_value, err_message


def index_stats(request):
    form_class = FilterSearchForm
    model = Transaction
    template = get_template('index_stats.html')
    data = {}
    kwargs = {}
    form = form_class(request.POST or None)
    if form.is_valid():
        my_date = form.cleaned_data['date']
        my_curr = form.cleaned_data['currency']
        my_reso = form.cleaned_data['resource']
        # print my_date, my_curr,my_reso
        if my_date:
            kwargs['date__date'] = my_date
        if my_curr:
            kwargs['currency_to'] = my_curr
        if my_reso:
            kwargs['resource_from'] = my_reso
        # print kwargs

    # print transaction_list.query
    total_bought_count = model.objects.filter(type='B',
                                              **kwargs).count()

    sum_bought = model.objects.filter(type='B',
                                      **kwargs
                                      ).aggregate(total=Sum(F('total'))
                                                  )

    amount_bought = model.objects.filter(type='B',
                                         **kwargs
                                         ).aggregate(total=Sum(F('amount'))
                                                     )

    profit_bought = model.objects.filter(
        type='B',
        **kwargs
    ).aggregate(
        total=Sum(
            (F('kraken_price') *
             F('amount')
             ) - F('total')
        )
    )

    total_sold_count = model.objects.filter(
        type='S',
        **kwargs
    ).count()

    sum_sold = model.objects.filter(
        type='S',
        **kwargs
    ).aggregate(
        total=Sum(F('total'))
    )

    amount_sold = model.objects.filter(
        type='S',
        **kwargs
    ).aggregate(
        total=Sum(F('amount'))
    )
    profit_sold = model.objects.filter(
        type='S',
        **kwargs
    ).aggregate(
        total=Sum(
            F('total') -
            (F('kraken_price') *
             F('amount'))
        )
    )

    data['sold'] = {"count": total_sold_count,
                    "amount": amount_sold["total"],
                    "total": sum_sold["total"],
                    "profit": profit_sold["total"]
                    }

    data['bought'] = {"count": total_bought_count,
                      "amount": amount_bought["total"],
                      "total": sum_bought["total"],
                      "profit": profit_bought["total"]
                      }

    return HttpResponse(template.render({'form': form,
                                         'data': data,
                                         'action': 'Stats Main'},
                                        request
                                        )
                        )
