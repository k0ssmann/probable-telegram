#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
import os
import shutil
import argparse
import json
import subprocess
from pathlib import Path
import keyring
from Shibboleth import Shibboleth, TUCServiceProvider, OPALServiceProvider, VCSServiceProvider
from scraper import opal_scraper, get_m3u8, get_ts

fn = 'content.json'

def write_content(key, val):
    if not Path(fn).exists():
        try:
            f = open(fn,"w")
            f.write("{}")
            logging.info('Json file for content has been created')
            f.close()
        except Exception as e:
            logging.error("Got unhandled exception %s" % str(e))
            sys.exit(1)
    try:
        with open(fn, "r") as read_file:
            data = json.load(read_file)
            if not "content" in data:
                data["content"] = {key: val}
            elif key in data["content"]:
                logging.error("Key " + key + " is already in use.")
                sys.exit(1)
            else:
                data["content"].update({key: val})
    except Exception as e:
        logging.error("Got unhandled exception %s" % str(e))
        sys.exit(1)
    
    try:
        with open(fn, "w") as write_file:
            json.dump(data, write_file, indent = 2)
    except Exception as e:
        logging.error("Got unhandled exception %s" % str(e))
        sys.exit(1)
    

def write_argument(arg, val):
    if not Path(fn).exists():
        try:
            f = open(fn,"w")
            f.write("{}")
            logging.info('Json file for content has been created')
            f.close()
        except Exception as e:
            logging.error("Got unhandled exception %s" % str(e))
            sys.exit(1)
    try:
        with open(fn, "r") as read_file:
            data = json.load(read_file)
            data[arg] = val
    except Exception as e:
        logging.error("Got unhandled exception %s" % str(e))
        sys.exit(1)
    
    try:
        with open(fn, "w") as write_file:
            json.dump(data, write_file, indent = 2)
    except Exception as e:
        logging.error("Got unhandled exception %s" % str(e))
        sys.exit(1)
        
def delete_from_json(key):
    if not Path(fn).exists():
        logging.ERROR(fn + "doesn't exist yet. See ./opal-scraper.py -h for help")
        sys.exit(1)
    
    try:
        with open(fn, "r") as read_file:
            data = json.load(read_file)
            content = data['content']
            content.pop(key)
            data['content'].update(content)
    except KeyError:
        logging.error("Key " + key + " was not found in " + fn)
        sys.exit(1)
    except Exception as e:
        logging.error("Got unhandled exception %s" % str(e))
        sys.exit(1)
            
    
    try:
        with open(fn, "w") as write_file:
            json.dump(data, write_file, indent = 2)
    except Exception as e:
        logging.error("Got unhandled exception %s" % str(e))
        sys.exit(1)


def update():
    fn = 'content.json'
    
    if not Path(fn).exists():
        logging.error(fn + " was not found. Terminating program.")
        sys.exit(1)
    else:
        try:
          with open(fn, "r") as read_file:
                data = json.load(read_file)
                if "user-agent" not in data.keys():
                    logging.error("No user agent was set.")
                    sys.exit(1)
                else:
                    username = data.get("username")
                    uagent = data.get("user-agent")
        except Exception as e:
            logging.error("Got unhandled exception %s" % str(e))
            sys.exit(1)
            
    shib = Shibboleth()
    shib.setUser(username)
    shib._headers.update({'User-Agent': uagent})
    TUC = TUCServiceProvider(shib)
    shib = TUC.connect()
    
    OPAL = OPALServiceProvider(shib)
    shib = OPAL.connect()
    
    VCS = VCSServiceProvider(shib)
    shib = VCS.connect()
    
    opal_scraper(shib)
    
    return 0

def download():
    fn = 'content.json'
    
    if not Path(fn).exists():
        logging.error(fn + " was not found. Terminating program.")
        sys.exit(1)
    else:
        try:
          with open(fn, "r") as read_file:
                data = json.load(read_file)
                if "user-agent" not in data.keys():
                    logging.error("No user agent was set.")
                    sys.exit(1)
                else:
                    username = data.get("username")
                    uagent = data.get("user-agent")
                    contents = data.get("content")
        except Exception as e:
            logging.error("Got unhandled exception %s" % str(e))
            sys.exit(1)
    
    
    shib = Shibboleth()
    shib.setUser(username)
    shib._headers.update({'User-Agent': uagent})
    TUC = TUCServiceProvider(shib)
    shib = TUC.connect()

    VCS = VCSServiceProvider(shib)
    shib = VCS.connect()
    
    for key in contents:
        
        path = "./{key}".format(key=key)
        
        try:
            os.mkdir(path)
        except OSError:
            logging.error("Creation of the directory %s failed" % path)
        else:
            logging.info("Successfully created the directory %s " % path)
        
        
        for idx, medium in enumerate(contents[key].get("media")):
            
            if not medium.get("downloaded"):
                path = "./{key}/tmp_{sharekey}".format(key=key, sharekey=medium.get("sharekey"))
                
                try:
                    os.mkdir(path)
                except OSError:
                    logging.error("Creation of the directory %s failed" % path)
                else:
                    logging.info("Successfully created the directory %s " % path)
                
                try:
                    get_m3u8(key, medium.get("sharekey"), path, shib)
                    get_ts(key, medium.get("sharekey"), path, shib)
                    contents[key]["media"][idx]["downloaded"] = True
                    data["content"].update(contents)
                except Exception as e:
                    logging.error("Got unhandled exception %s" % str(e))
                    sys.exit(1)
                
                try:
                    with open(fn, "w") as write_file:
                        json.dump(data, write_file, indent = 2)
                except Exception as e:
                    logging.error("Got unhandled exception %s" % str(e))
                    sys.exit(1)
            
    return 0


def convert():
    fn = 'content.json'
    
    if not Path(fn).exists():
        logging.error(fn + " was not found. Terminating program.")
        sys.exit(1)
    else:
        try:
          with open(fn, "r") as read_file:
                data = json.load(read_file)
                contents = data.get("content")
        except Exception as e:
            logging.error("Got unhandled exception %s" % str(e))
            sys.exit(1)
            
    for key in contents:
        path = "./{key}".format(key=key)
        for idx, medium in enumerate(contents[key].get("media")):
            if medium.get("downloaded"):
                dir_path = (path+"/tmp_{sharekey}").format(sharekey=medium.get("sharekey"))
                if os.path.exists(dir_path):                           
                    files = dir_path+"/files.txt"
                    subprocess.run(['ffmpeg', '-f', 'concat', '-i', files, '-c', 'copy', 
                                     (path+"/{sharekey}.mkv").format(sharekey=medium.get("sharekey"))])
                    shutil.rmtree(dir_path)
    
if __name__ == '__main__':
        
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", help="increase output verbosity", 
                        action="count", default=2)
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--user", help="set username and password", type=str, nargs=2, 
                       metavar=('USERNAME', 'PASSWORD'))
    group.add_argument("--uagent", help="set user agent", type=str)
    group.add_argument("--delete", help="delete source", type=str, metavar=('LABEL'))
    group.add_argument("--add", help="add OPAL repository", 
                       type=str, nargs=2, metavar=('LABEL','REPO'))
    group.add_argument("--update", help="update contents", action="store_true")
    group.add_argument("--download", help="download contents", action="store_true")
    group.add_argument("--convert", help="Convert transport streams", action="store_true")
    
    
    args = parser.parse_args()
    
    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s', 
                                  '%Y-%m-%d %H:%M:%S')

    if args.verbosity >= 5:
        root.setLevel(logging.CRITICAL)
        handler.setLevel(logging.CRITICAL)
    elif args.verbosity >= 4:
        root.setLevel(logging.ERROR)
        handler.setLevel(logging.ERROR)
    elif args.verbosity >= 3:
        root.setLevel(logging.WARNING)
        handler.setLevel(logging.WARNING)
    elif args.verbosity >= 2:
        root.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
    else:
        root.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    
    handler.setFormatter(formatter)
    root.addHandler(handler)

    if args.user:
        logging.info("Set username and password.")
        write_argument("username", args.user[0])
        keyring.set_password("system", args.user[0], args.user[1])
        
    if args.uagent:
        logging.info("Set user agent.")
        write_argument("user-agent", args.uagent)

    if args.add:
        logging.info("Add " + args.add[0] + " to contents.")
        label = args.add[0]
        target = {'target': args.add[1]}
        write_content(label,  target)
        
    if args.delete:
        logging.info("Remove " + args.delete + ' from contents')
        delete_from_json(args.delete)
        
    if args.update:
        logging.info("Update contents...")
        update()
    if args.download:
        logging.info("Download contents...")
        download()
    if args.convert:
        logging.info("Convert videos")
        convert()

    
    if len(sys.argv) == 1:
        print("Usage: opal-scraper.py [options]")
        print("\nGetting help:")
        print("\t-h\t -- print options")

