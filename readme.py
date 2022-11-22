# <!--# Setup-->

#<!--Copy and paste your code for your News Scraper website from the Backend Module to this folder-->
from urllib.request import urlopen
from datetime import datetime
from bs4 import BeautifulSoup
from flask import jsonify 
import json
import psycopg2
import psycopg2.extras

def get_db_connection():
  try:
    conn = psycopg2.connect("user=postgres password=input('Enter DB password') host=news-scraper-db-callum.c1i5dspnearp.eu-west-2.rds.amazonaws.com")
    return conn
  except:
    print("Error connecting to database.")

conn = get_db_connection()

def delete_all_data(table):
    try:
        if conn != None:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {table};")
            curs.execute(f"alter sequence {table}_id_seq restart with 1;")
            conn.commit()
    except:
        return "Unable to action this request", 400
    else:
        return 'No connection to database', 500

def get_html(url):
    if url:
        page = urlopen(url)
        html_bytes = page.read()
        html = html_bytes.decode("utf_8")
        return html
    else:
        "unable to process", 400

def parse_data_articles(domain_url, html):
    soup = BeautifulSoup(html, "html.parser")
    html = soup.select(".ssrcss-1yh0utg-PromoContent")
    articles = []

    for div in html:
        try:
            header = div.select('.e1f5wbog0')
            href = header[0].get('href')
            
            tag_name = div.select('.ecn1o5v1')[0]
            
            title = header[0].get_text()
            tag = tag_name.get_text()
        
        except:
            print('none found')
        if 'http' not in href:
            href = domain_url + href
        articles.append({"title": title, "url": href, "tag": tag})
    
    return articles


def add_stories_to_database(story):
    if conn != None:
        try:
            for i in range(len(story)):
                curs = conn.cursor()
                curs.execute("INSERT INTO stories(title, url, created_at, updated_at) VALUES (%s, %s, current_timestamp, current_timestamp) ON CONFLICT DO NOTHING;", ((story[i]['title']), (story[i]['url'])))
                conn.commit()
                curs.close()
        except:
            return "Unable to action this request", 400
    else:
         return "No connection to database", 500


def add_to_metadata(stories):
    query = "INSERT INTO metadata (story_id, tag_id) VALUES ((SELECT id FROM stories WHERE title = %s), (SELECT id FROM tags WHERE description = %s));"
    if conn != None:
        try:
            for i in range(len(stories)):
                curs = conn.cursor()
                curs.execute(query, (stories[i]['title'], stories[i]['tag']))
                conn.commit()
        except:
            return "Unable to action this request", 400
    else:
        return 'No connection to database', 500
    
def add_tags_to_database(stories):
    list_of_tags = []

    for i in range(len(stories)):
        list_of_tags.append(stories[i]['tag'])
# <!--        #Create a dictionary, using the List items as keys. This will automatically remove any duplicates because dictionaries cannot have duplicate keys.-->
        new = list(dict.fromkeys(list_of_tags))

    if conn != None:
        try:
            for i in range(len(new)):
                curs = conn.cursor()
                curs.execute("INSERT INTO tags(description) VALUES (%s)", [new[i]])
                conn.commit()
        except:
            return "Unable to action this request", 400
    else:
        return 'No connection to database', 500


if __name__ == "__main__":
    bbc_url = "http://www.bbc.co.uk/"
    bbc_html_doc = get_html(bbc_url)
    stories = parse_data_articles(bbc_url, bbc_html_doc)
    # add_stories_to_database(stories)
    # add_tags_to_database(stories)
    # add_to_metadata(stories)
# <!--    # delete_all_data('tags')-->
