#############################
#
# JSON FORMAT:
# "tenant_id":"",
# "grant_type":"client_credentials",
# "client_id":"",
# "client_secret":"",
# "resource":"https://management.microsoftazure.com/",
# "bearerToken":"undefined"
#
#############################

#!/usr/bin/env python


import os
import json
import requests
import wget
import time
import smtplib
import PyPDF2

path = "/"
apiversion = '2017-02-27-preview'
errorLog = ""


def login_url(account):
    return {
        'cn/' : "https://login.partner.microsoftonline.cn/",
        'de/' : "https://login.microsoftonline.de/",
        'com/' : "https://login.microsoftonline.com/"
    }[(account['resource'].split(".")[2])]

def login(account):
    url = login_url(account)+account['tenant_id']+'/oauth2/token'
    try:
        response = requests.post(url, data=account)
    except requests.exceptions.RequestException as e:
        errorLog += e
    account['bearerToken'] = "Bearer " + json.loads(response.text)['access_token']

def get_subscriptions(account):
    url = account['resource']+"subscriptions/?api-version=2017-05-10"
    list = []
    try:
        response = requests.get(url, headers={"Authorization": account['bearerToken']})
    except requests.exceptions.RequestException as e:
        errorLog += e
    for subscript in json.loads(response.text)['value']:
        list.append(subscript['subscriptionId'])
    return list

def get_invoice_name(account, subscription):
    url = account['resource']+'subscriptions/'+subscription+'/providers/Microsoft.Billing/invoices/?api-version='+apiversion
    try:
        response = requests.get(url, headers={"Authorization": account['bearerToken']})
    except requests.exceptions.RequestException as e:
        errorLog += e
    currentYearMonth = time.strftime("%Y%m")
    if response.status_code == 404:
        return None
    for reportedInvoices in json.loads(response.text)['value']:
        if reportedInvoices['name'].startswith(currentYearMonth):
            return reportedInvoices['name']

def download_invoice(account, name, subscription):
    url = account['resource']+'subscriptions/'+subscription+'/providers/Microsoft.Billing/invoices/'+name+'?api-version='+apiversion
    try:
        response = requests.get(url, headers={"Authorization": account['bearerToken']})
    except requests.exceptions.RequestException as e:
        errorLog += e
    url = json.loads(response.text)['properties']['downloadUrl']['url']
    invoice = wget.download(url)
    return invoice

def pull_out_total(filename):
    pdfObj = open(filename,'rb')
    pdfreader = PyPDF2.PdfFileReader(pdfObj)
    pageObj = pdfreader.getPage(pdfreader.numPages-1)
    string = pageObj.extractText()
    total = string.split("Grand Total")[1].split('\n')[1]
    return total

def write_billing_summary(fileObject, total, subscription):
    name = fileObject.name.split(".")[0]
    name += " $" + total
    with open("emailtext.text","a") as emailfile:
        emailfile.write("\n")
        emailfile.write(subscription + " " + name)
        if errorLog:
            emailfile.write(errorLog)


def main():
    for accountlist in os.listdir(path):
        if accountlist.endswith(".json"):
            fileObject = open(accountlist,'r')
            account = json.loads(fileObject.read())
            login(account)
            subscriptions = get_subscriptions(account)
            for subscription in subscriptions:
                name = get_invoice_name(account, subscription)
                if name is None:
                    write_billing_summary(fileObject, '0', subscription)
                if name != None:
                    download_invoice_name = download_invoice(account, name, subscription)
                    total = pull_out_total(download_invoice_name)
                    write_billing_summary(fileObject, total, subscription)

if __name__ == '__main__':
    main()
