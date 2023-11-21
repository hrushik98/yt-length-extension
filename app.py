from flask import Flask, request, jsonify
from flask_cors import CORS  # Add this line



from datetime import timedelta
import isodate
import json
import re
import requests

app = Flask(__name__)
CORS(app) 

API_KEY = "AIzaSyAGvlIdDngJ0tYJ19d8mAj7JFcg1zqtXyw"
URL1 = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&fields=items/contentDetails/videoId,nextPageToken&key={}&playlistId={}&pageToken='
URL2 = 'https://www.googleapis.com/youtube/v3/videos?&part=contentDetails&id={}&key={}&fields=items/contentDetails/duration'

def get_id(playlist_link):
    p = re.compile('^([\S]+list=)?([\w_-]+)[\S]*$')
    m = p.match(playlist_link)
    if m:
        return m.group(2)
    else:
        return 'invalid_playlist_link'

def parse_duration(duration):
    return isodate.parse_duration(duration)

def format_timedelta(td):
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{:02} hours, {:02} minutes, {:02} seconds".format(hours, minutes, seconds)

def calculate_watch_time(playlist_url, api_key):
    playlist_id = get_id(playlist_url)

    next_page = ''
    total_duration = timedelta(0)
    speed_multipliers = [1, 1.25, 1.5, 1.75, 2]

    while True:
        vid_list = []

        try:
            results = json.loads(requests.get(URL1.format(api_key, playlist_id) + next_page).text)

            for x in results['items']:
                vid_list.append(x['contentDetails']['videoId'])
        except KeyError as e:
            print(f"Error: {e}")
            break

        url_list = ','.join(vid_list)

        try:
            op = json.loads(requests.get(URL2.format(url_list, api_key)).text)

            for x in op['items']:
                total_duration += parse_duration(x['contentDetails']['duration'])
        except KeyError as e:
            print(f"Error: {e}")
            break

        if 'nextPageToken' in results:
            next_page = results['nextPageToken']
        else:
            break

    results_text = []
    results_text.append(f'Total length of playlist: {format_timedelta(total_duration)}')

    for speed_multiplier in speed_multipliers:
        adjusted_duration = total_duration / speed_multiplier
        results_text.append(f'At {speed_multiplier}x: {format_timedelta(adjusted_duration)}')

    return results_text

@app.route('/cwt', methods=['POST'])
def calculate_watch_time_endpoint():
    data = request.get_json()
    playlist_url = data.get('playlist_url', '')
    results = calculate_watch_time(playlist_url, API_KEY)

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
