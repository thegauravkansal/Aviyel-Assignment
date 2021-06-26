## Opensource api for youtube search
from youtubesearchpython.__future__ import Search, Video,Playlist
import asyncio
import pandas as pd
import json
import time
from flask import Flask, request, jsonify
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
import pathlib
import flask_profiler

app = Flask(__name__)
app.config["DEBUG"] = False

app.config["flask_profiler"] = {
    "enabled": app.config["DEBUG"],
    "storage": {
        "engine": "sqlite"
    },
    "basicAuth":{
        "enabled": True,
        "username": "admin",
        "password": "admin"
    },
    "ignore": [
	    "^/static/.*"
	]
}

path = str(pathlib.Path(__file__).parent.absolute())

dirname = "logs"
if not os.path.exists(dirname):
        os.makedirs(dirname)
        
dirname = "data"
if not os.path.exists(dirname):
        os.makedirs(dirname)
        
#logger object  
logger = logging.getLogger("Youtube Search")
logger.setLevel(logging.INFO)

# create a file handler
filename = path.replace("\"","/") + "/logs/youtube_search.log"
handler = RotatingFileHandler(filename,mode='a',maxBytes=1024*1024*20,backupCount=2)
handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)
logger.addHandler(console_handler)

video_record_notfound = []
keyword = []
    
def flatten_json(data):
    '''Flatten nested records
        data: nested dictonary or nested json record
        return: flatten dict'''
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '->')
        elif type(x) is list:
            i = 0 ##level
            for a in x:
                flatten(a, name + str(i) + '->')
                i += 1
        else:
            out[name[:-2]] = x

    flatten(data)
    return out
    
async def search_video(video_list_record):
    ''' Fetch and process video details from the API
        video_list_record: list of video ids
    '''
        
    logger.info("fetching and processing video data ....")
    
    global video_record_notfound,keyword

    processed_video_record = []
    for video_id in video_list_record:
        video_path = 'https://www.youtube.com/watch?v='+video_id
        try:
            video = await Video.get(video_path)
            processed_video_record.append(flatten_json(video))
        except:
            video_record_notfound.append(video_id)
            logger.info(video_id+" record not found.")
            pass
        time.sleep(0.1)
        logger.info(video_id+" record fetched")
        filename = path.replace("\"","/") + "/" + "data/" + keyword +"/processed_video_data.csv"
    pd.DataFrame(processed_video_record).to_csv(filename,index=False)
    logger.info("video data fetched and processed.")

async def search_playlist(playlist_data):
    ''' Fetch and process playlist details from the API
        playlist_data: list of playlist ids
        return:
            list of video ids in a playlist
    '''
    
    logger.info("fetching and processing playlist data ....")
    
    global video_record_notfound,keyword

    processed_playlist_record = []
    for record in playlist_data:
        url= 'https://www.youtube.com/playlist?list='+record["id"]
        playlist = Playlist(url)
        #logger.info('Fetching videos from '+str(record["title"]))
        while playlist.hasMoreVideos:
            try:
                await playlist.getNextVideos()
                logger.info('Videos Retrieved: ' + str(len(playlist.videos)))
            except:
                video_record_notfound.append(record["id"])
                logger.info(record["id"]+" record not found.")
                pass
        for video in playlist.videos:
            flatten_record= flatten_json(video)
            flatten_record["playlist_id"] = record["id"]
            processed_playlist_record.append(flatten_record)
            
    processed_playlist_record = pd.DataFrame(processed_playlist_record)
    filename = path.replace("\"","/") + "/" + "data/" + keyword +"/processed_playlist_video_data.csv"
    processed_playlist_record.to_csv(filename,index=False)
    logger.info("playlist data fetched and processed.")
    return list(processed_playlist_record["id"])

async def search_youtube(query,sample_size):
    ''' Fetch and process youtube search details and playlist details
        query: keyword name or video id list
        sample_size: number of record that need to be fetched
        return: video id of all fetched records'''
        
    
    search = Search(query, limit=10)
    
    ## to store raw_search_data
    raw_data = []
    processed_data = []
    record_count = 0
    prev = 0
    logger.info("fetching and processing search data ....")
    while True:
        try:
            result = await search.next()
        except:
            pass
        
        prev = record_count
        record_count += len(result["result"])

        for record in result["result"]:
            raw_data.append(record)
            processed_data.append(flatten_json(record))
        
        '''If API return null record, we put the system to sleep'''
        if record_count == prev:
            logger.info("API constraint.")
            break
        if record_count >=sample_size:
            break
        logger.info(str(record_count)+" fetched and processed.")
    logger.info(str(record_count)+"records fetched and processed.")
    
    filename = path.replace("\"","/") + "/" + "data/" + query + "/unprocessed_raw_data.txt"
    dirname = "data"
    
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    
    with open(filename, "w") as fp:
        json.dump(raw_data, fp)
    processed_data = pd.DataFrame(processed_data)
    
    filename = path.replace("\"","/") + "/" + "data/" + query + "/processed_search_data.csv"
    processed_data.to_csv(filename,index=False)
    
    logger.info("search data stored successfully.")
    
    video_list_record = list(processed_data["id"][processed_data["type"]=="video"])
    
    logger.info("fetching video details from playlist...")
    playlist_data = processed_data[["id","title"]][processed_data["type"]=="playlist"]
    if not playlist_data.empty:
        playlist_video_id = await search_playlist(playlist_data[["id","title"]].to_dict("records"))
        video_list_record.extend(playlist_video_id)
    else:
        logger.info("No playlist found in the fetched records.")
    logger.info("details fetched from playlist.")
    
    return video_list_record

flask_profiler.init_app(app)

@app.route('/', methods=['POST'])
#@flask_profiler.profile()
def fetch_record():
    
    global video_record_notfound,keyword
    keyword = request.args.get("keyword")
    sample_size = request.args.get("sample_size")
    
    if not os.path.exists("data/"+keyword):
            os.makedirs("data/"+keyword)
        
    if not sample_size.isdigit():
        return jsonify({"status":"failure","message":"enter integer sample size"})
    else:
        sample_size = int(sample_size)
        video_list_record = asyncio.run(search_youtube(keyword, sample_size))
        asyncio.run(search_video(video_list_record))
        if video_record_notfound == []:
            status = True
        else:
            status = False
        return jsonify({'status':'success','video_record_notfound':status})

if __name__ == "__main__":
    
    app.run(port=5000, threaded=True)
