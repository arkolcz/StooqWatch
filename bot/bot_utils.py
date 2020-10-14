#!/usr/bin/python3

import os
import requests

from dotenv import load_dotenv
from bs4 import BeautifulSoup

def get_config_data(cfg, key):
    '''Get data from config.env file
        Parameters:
            cfg (str): config file name
            key (str): keyword

        Returns:
            str:value
        '''
    load_dotenv(cfg)
    return os.environ.get(key)


def get_response(url):
    '''Get response from website
        Parameters:
            url (str): URL address

        Returns:
            response object:res
    '''
    try:
        res = requests.get(url)
        res.encoding = res.apparent_encoding
        return res
    except Exception as err:
        raise Exception(f'Unable to esablish connection to the server (Error={err})')


def scrap_website(response):
    ''' Scrap website content
        Parameters:
            response (response object): response

        Returns:
            bs4 object:soup
    '''
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except HTMLParser.HTMLParseError as err:
        raise Exception(f'Unable to parse document (Error={err})')
