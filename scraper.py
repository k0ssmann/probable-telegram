#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import logging
import re
import sys
from pathlib import Path
import json

def get_course_nodes(shib, url):
    """
    BeautifulSoup can't parse JavaScript and RegEx is needed to extract
    links to course nodes.

    """
    response =  shib.session.get(url)    
    c = response.text
    p = re.compile("\"href\"\:\"(.*?)\"\,\"title\"\:\"(.*?)\"")
    course_nodes = p.findall(c)
    
    return course_nodes

def get_media(course_nodes, shib, src):
    """
    To download the video, we need the sharekey. The sharekey is in
    
    1. the url, if the video is embedded in the page
    2. inside an input tag on the VCS page
        
    """
    
    media = list()
    
    for node in course_nodes:
        iframeSrc = None
        response = shib.session.get(node[0])
        c = response.text
        
        soup = BeautifulSoup(c, 'html.parser')
        
        try:
            """
            Some video URLs are not offered in a list, but on a page 
            that is included as an iframe.
            """
            
            iframeSrc = soup.find('iframe').get('src')
            response = shib.session.get(src[0:33]+iframeSrc)
            c = response.text
            soup = BeautifulSoup(c, 'html.parser')
        except Exception:
            """
            TODO: Implement error handling
            """
            pass
        
        try:
            """
            iframe can have another iframe embedded that contains the embedded media.
            iframe source contains the sharekey
            """
            
            p = re.compile('embed\?key\=([A-Za-z0-9]+)')
            for iframe in soup.find_all('iframe'):
                embedded_media = iframe.get('src')
                sharekey = p.findall(embedded_media)
                response = shib.session.get(embedded_media)
                c = response.text
                soup = BeautifulSoup(c, 'html.parser')
                title = soup.find('video').get('data-piwik-title')
                media_dict = {'title': title,
                              'sharekey': sharekey[0],
                              'type': 'video'
                    }
                media.append(media_dict)
        except Exception:
            """
            TODO: Implement error handling
            """
            pass
            
            
        try:
            for link in soup.find_all("a", href=re.compile("videocampus")):
                """
                If there is no embedded video, there are probably links
                to the medium hosted on Videocampus Sachsen
                
                """
                
                url = link.get("href")
                response = shib.session.get(url)
                c = response.text
                soup = BeautifulSoup(c, 'html.parser')
                sharekey = soup.find('input', {'name':'sharekey'}).get('value')
                title = soup.find('video').get('data-piwik-title')
                
                media_dict = {
                    "title": title,
                    'sharekey': sharekey,
                    "type": 'video',
                    "downloaded": False
                    }
                media.append(media_dict)
        except Exception:
            """
            TODO: Implement error handling
            """
            pass
            
    return media

def opal_scraper(shib):
    
    fn = 'content.json'
    
    if not Path(fn).exists():
        logging.error(fn + " was not found. Terminating program.")
        sys.exit(1)
    else:
        try:
          with open(fn, "r") as read_file:
                data = json.load(read_file)
                content = data.get("content")
        except Exception as e:
            logging.error("Got unhandled exception %s" % str(e))
            sys.exit(1)
            
    
    """
    TODO:
        - Check if video is already in there
    """
            
    for key in content:
        d = content.get(key)
        logging.info("Checking for content for " + key)
        course_nodes = get_course_nodes(shib, d.get("target"))
        media = get_media(course_nodes, shib, d.get("target"))
        content[key]["media"] = media
    
    data["content"].update(content)
    
    try:
        with open(fn, "w") as write_file:
            json.dump(data, write_file, indent = 2)
    except Exception as e:
        logging.error("Got unhandled exception %s" % str(e))
        sys.exit(1)
    
    return 0


def download_file(url, path, shib):
    with shib.session.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return 0

def get_m3u8(key, sharekey, path, shib):
    
    
    logging.info("%s: Download m3u8 for %s" % (key, sharekey))
    m3u8_url = "https://videocampus.sachsen.de/media/hlsMedium/key/{sharekey}/format/auto/ext/mp4/learning/0/path/m3u8".format(sharekey=sharekey)
    m3u8_path = path + "/{sharekey}.m3u8".format(sharekey=sharekey)
    download_file(m3u8_url, m3u8_path, shib)
    
    with open(m3u8_path) as file:
        lines = [line.rstrip() for line in file]

    m3u8mp4_url = (m3u8_url[0:-4]+lines[7]).format(sharekey=sharekey)
    m3u8mp4_path = path + "/{sharekey}_mp4.m3u8".format(sharekey=sharekey)
    download_file(m3u8mp4_url, m3u8mp4_path, shib)
    
    
    return 0
    
def get_ts(key, sharekey, path, shib):
    url = "https://videocampus.sachsen.de/media/hlsMedium/key/{sharekey}/format/auto/ext/mp4/learning/0/path/".format(sharekey=sharekey)    
    m3u8mp4_path = path + "/{sharekey}_mp4.m3u8".format(sharekey=sharekey)

    with open(m3u8mp4_path) as file:
        lines = [line.rstrip() for line in file]
    

    
    ts_keys = [ x for x in lines if "EXT" not in x]
    
    logging.info("%s: Write files.txt for %s" % (key, sharekey))
    
    with open(path + "/files.txt", "w") as text_file:
        for ts in ts_keys:
            print(f"file '{ts}' ", file=text_file)
    
    for tkey in ts_keys:
        logging.info("%s: Download %s" % (key, tkey))
        durl = url+tkey
        ts_path = path+"/"+tkey
        download_file(durl, ts_path, shib)
        
    return 0