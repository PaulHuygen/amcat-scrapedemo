#!/usr/bin/env python
###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Lesser General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Lesser General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################
# wikinewsscraper.py -- convert wikinewspages into json for Amcat
# 20131215 Paul Huygen
"""
Demo to use api.py to upload scraped news-articles
"""

from __future__ import unicode_literals, print_function, absolute_import
import logging
import argparse
from bs4 import BeautifulSoup
import urllib2, requests
from urlparse import urljoin
import re
import json
from api import AmcatAPI

#logging.basicConfig(level=logging.DEBUG)

BASEURL = 'http://en.wikinews.org'
default_host = 'http://localhost'
default_user = 'amcat'
default_passwd = 'amcat'
default_project = '1'
default_articleset = 'Testset'
default_provenance = 'wikipedia.org'
default_init_url = 'http://en.wikinews.org/wiki/Category:Public_domain_articles'


def get_arguments():
  parser = argparse.ArgumentParser(description='Scrape wikinews for Amcat.')
  parser.add_argument('--host', help='Amcat webservice URL', default = default_host)
  parser.add_argument('--user', help='Username in Amcat',  default = default_user)
  parser.add_argument('--passwd', help='Password',  default = default_passwd)
  parser.add_argument('--project', help='Project id',  default = default_project)
  parser.add_argument('--aset', help='Articleset-name',  default = default_articleset)
  parser.add_argument('--provenance', help='Provenance of articles' , default=default_provenance)
  parser.add_argument('--url', help='URL of first index-page' , default=default_init_url)
  args = parser.parse_args()
  return [args.host, args.user, args.passwd, args.aset, args.project, args.provenance, args.url]

def get_article_urls(init_url):
  index_url = init_url
  while index_url != None:
     r = requests.get(index_url)
     sec1 = BeautifulSoup(r.text)
     sec2 = sec1.find(id='mw-content-text')
     index_soup = sec2.find(id = 'mw-pages')
     
     for li in index_soup.find_all('li'): 
        for a in li.find_all('a', href = True):
           yield urljoin(init_url, a['href'])
     
     
     index_url = None
     for a in index_soup.find_all('a', href = True):
         if len(a.contents) > 0 :
             if re.match('^next [0-9]+$', a.contents[0]):
                 index_url = urljoin(init_url, a['href'])
                 break

     

def scrape_article(url):
    r = requests.get(url)
    full_article_soup = BeautifulSoup(r.text)
    art_soup = full_article_soup.find(id='content')
    txt_soup = art_soup.find(id='mw-content-text')
    
    title_head = art_soup.find(id = 'firstHeading')
    title_span = title_head.contents[0]
    title = title_span.contents[0]
    
    date_soup = txt_soup.find(id = 'publishDate')
    try:
      pub_date = date_soup['title']
    except TypeError:
      pub_date = '2000-01-01'
    
    text = txt_soup.get_text()
    
    article = dict( headline =  title
                  , medium   =  'en.wikinews.org'
                  , text     =  text
                  , date     =  pub_date
                  )
    return article
    

def upload_article(project, articleset, article):
     print( "To add article dated {d}".format(d=article["date"]))
     articles = api.create_articles(project=project, articleset=articleset["id"], json_data=article)
#      print( "Added {n} articles to set {setid}".format(n=len(articles), setid=aset["id"]))
#      print( "Added article dated {d} to set {setid}".format(d=articles["date"], setid=aset["id"]))
     return

[host, user, passwd, aset, project, provenance, init_url] = get_arguments()

print( "User      : " + user)
print( "Password  : " + passwd)
print( "aset      : " + aset)
print( "project   : " + project)
print( "provenance: " + provenance)
print( "init-url  : " + init_url)

api = AmcatAPI(host, user, passwd)
aset = api.create_set(project=project, name=aset, provenance=provenance)

for art_url in get_article_urls(init_url):
   upload_article(project, aset, scrape_article(art_url))
