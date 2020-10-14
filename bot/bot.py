#!/usr/bin/python3


import sys

sys.path.append('..')

import discord
import bot_utils
import re
import asyncio
import logging
from discord.ext import tasks
from constants import CFG_FILE, PAGE_URL, MAX_MSG_LENGTH


class Bot(discord.Client):

    def __init__(self):
        super().__init__()
        self.channel = None
        # List of articles ID from main page
        self.articles_ids = []
        # ID of latest article published on discord
        self.latest_article_id = ''

        log_dir = str(bot_utils.get_config_data(CFG_FILE, 'LOG_DIR'))
        logging.basicConfig(filename=log_dir,
                            encoding='utf-8',
                            level=logging.DEBUG,
                            format='%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

    async def on_ready(self):
        print(f'Started as {self.user}')
        logging.info(f'Started as {self.user}')
        channel_id = int(bot_utils.get_config_data(CFG_FILE, 'CHANNEL_ID'))
        if channel_id is None:
            logging.error(f'Unable to retrieve channel id from config file: {CFG_FILE}')
            raise Exception(f'Unable to retrieve channel id from config file: {CFG_FILE}')
        self.channel = self.get_channel(channel_id)
        self.publish_articles.start()

    @tasks.loop(seconds=10.0, reconnect=True)
    async def publish_articles(self):
        try:
            await self.wait_until_ready()
            articles = self.get_articles()
            for title, content in articles:
                messages = self.create_discord_messages(title, content)
                for msg in messages:
                    await self.channel.send(msg)
        except Exception as err:
            logging.error(err)

    def create_discord_messages(self, title, content):
        ''' Create list of messages with discord decorators and
            proper length
            Parameters:
                title (str): article title
                content (str): article title

            Returns:
                messages (list): List of discord messages
        '''
        messages = []
        # Split messages so they can fit into discord message buffer
        title = [title[i:i+(MAX_MSG_LENGTH-4)] for i in range(0, len(title), MAX_MSG_LENGTH-4)]
        content = [content[i:i+(MAX_MSG_LENGTH-6)] for i in range(0, len(content), MAX_MSG_LENGTH-6)]

        # Add discord text decorators
        messages += ['**' + t + '**' for t in title]
        messages += ['```' + c + '```' for c in content]

        return messages

    def get_articles(self):
        ''' Get list od articles to publish

            Returns:
                article_list (list): List of tuples (article_title, article_content)
        '''
        res = bot_utils.get_response(PAGE_URL)
        page = bot_utils.scrap_website(res)
        self.find_newest_articles(page)
        articles_ids = self.find_unpublished_articles()
        return self.get_article_content(articles_ids)

    def find_newest_articles(self, page):
        ''' Look for newest articles from the main page and store
        thier IDs in class variable current_articles[]

            Paramteres:
                page (bs4 object): stooq.pl main page

            Returns:
                None
        '''
        current_articles = []
        for link in page.find_all('a'):
            if re.match(r'mol/\?id\=', link.get('href')):
                article_id = re.findall(r'id=(.*)', link.get('href')).pop(0)
                self.articles_ids.append(article_id)

    def find_unpublished_articles(self):
        ''' Compare current articles IDs from main page
            with ID of lastest published article on discord

            Returns:
                articles_to_publish (list): List of IDs
        '''
        articles_to_publish = []
        # Iterate from the oldest to the newest article
        for i in reversed(self.articles_ids):
            # Find articles that were not published on discord by
            # comparing thier ids with the latest article id that was published
            if i > self.latest_article_id:
                self.latest_article_id = i
                articles_to_publish.append(i)
        return articles_to_publish

    def get_article_content(self, articles_ids):
        ''' Get article title and content

            Parameters:
                articles_ids (list): List of unpublished articles IDs

            Returns:
                article_list (list): List of tuples (article_title, article_content)
        '''
        article_list = []
        for i in articles_ids:
            res = bot_utils.get_response(PAGE_URL + 'mol/?id=' + i)
            subpage = bot_utils.scrap_website(res)

            title = subpage.find('font', id='f22').text
            content = subpage.find('font', id='f13').text

            article_list.append((title, content))
        return article_list


if __name__ == "__main__":
    token = bot_utils.get_config_data(CFG_FILE, 'BOT_TOKEN')
    if token is None:
        logging.error(f'Unable to retrieve channel id from config file: {CFG_FILE}')
        raise Exception(f'Unable to retrieve token from config file: {CFG_FILE}')

    bot = Bot()
    bot.run(token)