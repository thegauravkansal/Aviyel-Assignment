## Opensource api for youtube search
from youtubesearchpython.__future__ import Search, Video,Playlist
import asyncio
import pandas as pd
import json
import time

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
        
    print("fetching and processing video data ....")
    processed_video_record = []
    for video_id in video_list_record:
        video_path = 'https://www.youtube.com/watch?v='+video_id
        try:
            video = await Video.get(video_path)
            processed_video_record.append(flatten_json(video))
        except:
            print("Unable to fetch record",video_id,"<------------------------ERROR")
            pass
        time.sleep(0.1)
        print(video_id,"record fetched")
    pd.DataFrame(processed_video_record).to_csv("data/processed_video_data.csv",index=False)
    print("video data fetched and processed.")

async def search_playlist(playlist_data):
    ''' Fetch and process playlist details from the API
        playlist_data: list of playlist ids
        return:
            list of video ids in a playlist
    '''
    
    print("fetching and processing playlist data ....")
    processed_playlist_record = []
    for record in playlist_data:
        url= 'https://www.youtube.com/playlist?list='+record["id"]
        playlist = Playlist(url)
        print('Fetching videos from',record["title"])
        while playlist.hasMoreVideos:
            try:
                await playlist.getNextVideos()
                print(f'Videos Retrieved: {len(playlist.videos)}')
            except:
                print("Unable to fetch record",record["id"],"<------------------------ERROR")
                pass
        for video in playlist.videos:
            flatten_record= flatten_json(video)
            flatten_record["playlist_id"] = record["id"]
            processed_playlist_record.append(flatten_record)
            
    processed_playlist_record = pd.DataFrame(processed_playlist_record)
    processed_playlist_record.to_csv("data/processed_playlist_video_data.csv",index=False)
    print("playlist data fetched and processed.")
    return list(processed_playlist_record["id"])

async def search_youtube(query,sample_size):
    ''' Fetch and process youtube search details and playlist details
        query: keyword name or video id list
        sample_size: number of record that need to be fetched
        return: video id of all fetched records'''
        
    
    search = Search(query)
    
    ## to store raw_search_data
    raw_data = []
    processed_data = []
    record_count = 0
    prev = 0
    print("fetching and processing search data ....")
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
            print("API constraint. Please start from fresh.")
            break
        if record_count >=sample_size:
            break
        print(str(record_count)," fetched and processed.")
    print(str(record_count),"records fetched and processed.")
    
    with open("data/unprocessed_raw_data.txt", "w") as fp:
        json.dump(raw_data, fp)
    processed_data = pd.DataFrame(processed_data)
    processed_data.to_csv("data/processed_search_data.csv",index=False)
    print("search data stored successfully.")
    
    video_list_record = list(processed_data["id"][processed_data["type"]=="video"])
    
    print("fetching video details from playlist...")
    playlist_data = processed_data[["id","title"]][processed_data["type"]=="playlist"]
    if not playlist_data.empty:
        playlist_video_id = await search_playlist(playlist_data[["id","title"]].to_dict("records"))
        video_list_record.extend(playlist_video_id)
    else:
        print("No playlist found in the fetched records.")
    print("details fetched from playlist.")
    
    return video_list_record

if __name__ == "__main__":
    
    '''To ensure correct data is entered'''
    while True: 
        try:
            query, sample_size = input("Enter a keyword:"), int(input("Enter a record size:"))
            break
        except ValueError:
            print("\nInvalid Entry. Please try again...")
            
    video_list_record = asyncio.run(search_youtube(query, sample_size))
    asyncio.run(search_video(video_list_record))
