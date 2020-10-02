#!/usr/bin/python3


import sys

sys.path.append('..')

import discord
import bot_utils
import re
from discord.ext import tasks
from constants import CFG_FILE, PAGE_URL


class Bot(discord.Client):

    def __init__(self):
        super().__init__()
        self.channel = None
        # List of articles ID from main page
        self.articles_ids = []
        # ID of latest article published on discord
        self.latest_article_id = ''

    async def on_ready(self):
        print(f'Started as {self.user}')

        channel_id = int(bot_utils.get_config_data(CFG_FILE, 'CHANNEL_ID'))
        if channel_id is None:
            raise Exception(f'Unable to retrieve channel id from config file: {CFG_FILE}')
        self.channel = self.get_channel(channel_id)
        self.background_loop.start()

    @tasks.loop(seconds=10.0, reconnect=True)
    async def background_loop(self):
        await self.wait_until_ready()
        articles = self.get_articles()
        for title, content in articles:
            message = '**' + title + '**'
            await self.channel.send(message)
            if len(content) > 0:
                message = '```' + content + '```'
                await self.channel.send(message)

    def get_articles(self):
        res = bot_utils.get_response(PAGE_URL)
        page = bot_utils.scrap_website(res)
        self.find_newest_articles(page)
        articles = self.find_unpublished_articles()
        articles = self.get_article_content(articles)
        return articles

    def find_newest_articles(self, page):
        '''
        Look for newest articles from the main page and store thier 
        IDs in current_articles[]
        '''
        current_articles = []
        for link in page.find_all('a'):
            if re.match(r'mol/\?id\=', link.get('href')):
                article_id = re.findall(r'id=(.*)', link.get('href')).pop(0)
                self.articles_ids.append(article_id)

    def find_unpublished_articles(self):
        articles_to_publish = []
        # Iterate from the oldest to the newest article
        for i in reversed(self.articles_ids):
            # Find articles that were not published on discord by
            # comparing thier ids with the latest article id that was published
            if i > self.latest_article_id:
                self.latest_article_id = i
                articles_to_publish.append(i)
        return articles_to_publish
        
    def get_article_content(self, articles):
        article_list = []
        for i in articles:
            res = bot_utils.get_response(PAGE_URL + 'mol/?id=' + i)
            subpage = bot_utils.scrap_website(res)

            title = subpage.find('font', id='f22').text
            content = subpage.find('font', id='f13').text

            article_list.append((title, content))
        return article_list

    async def publish_articles(self, articles):
        for title, content in articles:
            message = '**' + title + '**'
            await channel.send(message)
            if len(content) > 0:
                message = '```' + content + '```'
                await channel.send(message)

if __name__ == "__main__":
    token = bot_utils.get_config_data(CFG_FILE, 'BOT_TOKEN')
    if token is None:
        raise Exception(f'Unable to retrieve token from config file: {CFG_FILE}')

    bot = Bot()
    bot.run(token)