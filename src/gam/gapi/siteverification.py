import json
import sys
from urllib.parse import urlencode

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import fileutils
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi import errors as gapi_errors
from gam.gapi.directory import customer as gapi_directory_customer
from gam import transport
from gam import utils

import gam


def build():
    return gam.buildGAPIObject('siteVerification')


def create():
    verif = build()
    a_domain = sys.argv[3]
    txt_record = gapi.call(verif.webResource(),
                           'getToken',
                           body={
                               'site': {
                                   'type': 'INET_DOMAIN',
                                   'identifier': a_domain
                               },
                               'verificationMethod': 'DNS_TXT'
                           })
    print(f'TXT Record Name:   {a_domain}')
    print(f'TXT Record Value:  {txt_record["token"]}')
    print()
    cname_record = gapi.call(verif.webResource(),
                             'getToken',
                             body={
                                 'site': {
                                     'type': 'INET_DOMAIN',
                                     'identifier': a_domain
                                 },
                                 'verificationMethod': 'DNS_CNAME'
                             })
    cname_token = cname_record['token']
    cname_list = cname_token.split(' ')
    cname_subdomain = cname_list[0]
    cname_value = cname_list[1]
    print(f'CNAME Record Name:   {cname_subdomain}.{a_domain}')
    print(f'CNAME Record Value:  {cname_value}')
    print('')
    webserver_file_record = gapi.call(
        verif.webResource(),
        'getToken',
        body={
            'site': {
                'type': 'SITE',
                'identifier': f'http://{a_domain}/'
            },
            'verificationMethod': 'FILE'
        })
    webserver_file_token = webserver_file_record['token']
    print(f'Saving web server verification file to: {webserver_file_token}')
    fileutils.write_file(webserver_file_token,
                         f'google-site-verification: {webserver_file_token}',
                         continue_on_error=True)
    print(f'Verification File URL: http://{a_domain}/{webserver_file_token}')
    print()
    webserver_meta_record = gapi.call(
        verif.webResource(),
        'getToken',
        body={
            'site': {
                'type': 'SITE',
                'identifier': f'http://{a_domain}/'
            },
            'verificationMethod': 'META'
        })
    print(f'Meta URL:               http://{a_domain}/')
    print(f'Meta HTML Header Data:  {webserver_meta_record["token"]}')
    print()


def info():
    verif = build()
    sites = gapi.get_items(verif.webResource(), 'list', 'items')
    if sites:
        for site in sites:
            print(f'Site: {site["site"]["identifier"]}')
            print(f'Type: {site["site"]["type"]}')
            print('Owners:')
            for owner in site['owners']:
                print(f' {owner}')
            print()
    else:
        print('No Sites Verified.')


def update():
    verif = build()
    a_domain = sys.argv[3]
    verificationMethod = sys.argv[4].upper()
    if verificationMethod == 'CNAME':
        verificationMethod = 'DNS_CNAME'
    elif verificationMethod in ['TXT', 'TEXT']:
        verificationMethod = 'DNS_TXT'
    if verificationMethod in ['DNS_TXT', 'DNS_CNAME']:
        verify_type = 'INET_DOMAIN'
        identifier = a_domain
    else:
        verify_type = 'SITE'
        identifier = f'http://{a_domain}/'
    body = {
        'site': {
            'type': verify_type,
            'identifier': identifier
        },
        'verificationMethod': verificationMethod
    }
    try:
        verify_result = gapi.call(
            verif.webResource(),
            'insert',
            throw_reasons=[gapi_errors.ErrorReason.BAD_REQUEST],
            verificationMethod=verificationMethod,
            body=body)
    except gapi_errors.GapiBadRequestError as e:
        print(f'ERROR: {str(e)}')
        verify_data = gapi.call(verif.webResource(), 'getToken', body=body)
        print(f'Method:  {verify_data["method"]}')
        print(f'Expected Token:      {verify_data["token"]}')
        if verify_data['method'] in ['DNS_CNAME', 'DNS_TXT']:
            simplehttp = transport.create_http()
            base_url = 'https://dns.google/resolve?'
            query_params = {}
            if verify_data['method'] == 'DNS_CNAME':
                cname_token = verify_data['token']
                cname_list = cname_token.split(' ')
                cname_subdomain = cname_list[0]
                query_params['name'] = f'{cname_subdomain}.{a_domain}'
                query_params['type'] = 'cname'
            else:
                query_params['name'] = a_domain
                query_params['type'] = 'txt'
            full_url = base_url + urlencode(query_params)
            (_, c) = simplehttp.request(full_url, 'GET')
            result = json.loads(c)
            status = result['Status']
            if status == 0 and 'Answer' in result:
                answers = result['Answer']
                if verify_data['method'] == 'DNS_CNAME':
                    answer = answers[0]['data']
                else:
                    answer = 'no matching record found'
                    for possible_answer in answers:
                        possible_answer['data'] = possible_answer['data'].strip(
                            '"')
                        if possible_answer['data'].startswith(
                                'google-site-verification'):
                            answer = possible_answer['data']
                            break
                        print(
                            f'Unrelated TXT record: {possible_answer["data"]}')
                print(f'Found DNS Record: {answer}')
            elif status == 0:
                controlflow.system_error_exit(1, 'DNS record not found')
            else:
                controlflow.system_error_exit(
                    status,
                    DNS_ERROR_CODES_MAP.get(status, f'Unknown error {status}'))
        return
    print('SUCCESS!')
    print(f'Verified:  {verify_result["site"]["identifier"]}')
    print(f'ID:  {verify_result["id"]}')
    print(f'Type: {verify_result["site"]["type"]}')
    print('All Owners:')
    try:
        for owner in verify_result['owners']:
            print(f' {owner}')
    except KeyError:
        pass
    print()
    print(
        f'You can now add {a_domain} or it\'s subdomains as secondary or domain aliases of the {GC_Values[GC_DOMAIN]} G Suite Account.'
    )
