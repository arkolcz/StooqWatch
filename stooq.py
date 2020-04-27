import discord
import re
import requests
import time
import asyncio
from bs4 import BeautifulSoup


 
########### StooqWatch: Discord Bot ############
client = discord.Client()
page_url = 'https://stooq.pl/'

current_articles = [] # List of article IDs
latest_article_id = ''
article_title = ''
article_content = ''

def find_newest_articles(page):
    '''
    Look for newest articles from the main page and store thier 
    IDs in current_articles[]
    '''
    global current_articles
    current_articles = []
    for link in page.find_all('a'):
        if re.match(r'mol/\?id\=', link.get('href')):
            article_id = re.findall(r'id=(.*)', link.get('href')).pop(0)
            current_articles.append(article_id)

def scrap_website(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def fetch_response(url):
    r = requests.get(url)
    r.encoding = r.apparent_encoding
    return r

def find_unpublished_articles():
    global current_articles
    global latest_article_id
    articles_to_publish = []
    # Iterate from the oldest to the newest article
    for i in reversed(current_articles):
        # Find articles that were not published on discord by
        # comparing thier ids with the latest article id that was published
        if i > latest_article_id:
            latest_article_id = i
            articles_to_publish.append(i)
    return articles_to_publish

def get_article():
    res = fetch_response(page_url)
    page = scrap_website(res)
    find_newest_articles(page)
    articles = find_unpublished_articles()
    messages_to_publish = create_discord_messages(articles)
    return messages_to_publish

def create_discord_messages(articles):
    messages = []
    for i in articles:
        res = fetch_response(page_url + 'mol/?id=' + i)
        subpage = scrap_website(res)
        title = subpage.find('font', id='f22').text
        messages.append('**' + title + '**')
        article_content = subpage.find('font', id='f13').text
        messages.append('```' + article_content + '```')
    return messages

def fetch_token():
    with open('token.txt', 'r') as f:
        lines = f.readlines()
        return lines.pop(0)

token = fetch_token()

async def publish_article():
    channel_id = 0 # Change to adequate channel_id
    channel = client.get_channel()
    await client.wait_until_ready()
    while True:
        messages = get_article()
        for msg in messages:
            if msg:
                await channel.send(msg)
        await asyncio.sleep(60)
    

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    client.loop.create_task(publish_article())

token = fetch_token()
client.run(token)

