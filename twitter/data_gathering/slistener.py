from tweepy.streaming import StreamListener
import json
import time
import sys
import pandas as pd
from sqlalchemy import create_engine

class SListener(StreamListener):
    #Initialize api and counter for number of tweets collected
    def __init__(self, api=None, fprefix='streamer'):
        self.api = api
        self.cnt = 0
        #create an engine to database
        self.engine = create_engine('sqlite:///app/tweets.sqlite')

#for each tweet streamed
def on_status(self,status):

    global full_text
    self.cnt += 1

    #parse the status object to JSON
    status_json = json.dumps(status._json)
    #convert the JSON string into dict
    status_data = json.loads(status_json)

    #initialize a list of potential full-text
    full_text_list = [status_data['text']]

    # add full-text field from all sources into the list
    if 'extended_tweet' in status_data:
        full_text_list.append(status_data['extended_tweet']['full_text'])
    if 'retweeted_status' in status_data and 'extended_tweet' in status_data['retweeted_status']:
        full_text_list.append(status_data['retweeted_status']['extended_tweet']['full_text'])
    if 'quoted_status' in status_data and 'extended_tweet' in status_data['quoted_status']:
        full_text_list.append(status_data['quoted_status']['extended_tweet']['full_text'])

     # only retain the longest candidate
        full_text = max(full_text_list, key=len)

    # extract time and user info
    tweets = {
        'created_at': status_data['created_at'],
        'text': full_text,
        'user': status_data['user']['description']
        }

    # uncomment the following to display tweets in the console
    print("Writing tweet # {} to the database".format(self.cnt))
    print("Tweet Created at: {}".format(tweets['created_at']))
    print("Tweets Content:{}".format(tweets['text']))
    print("User Profile: {}".format(tweets['user']))

    # convert into dataframe
    df = pd.DataFrame(tweets, index=[0])

    # convert string of time into date time obejct
    df['created_at'] = pd.to_datetime(df.created_at)

    # push tweet into database
    df.to_sql('tweet', con=self.engine, if_exists='append')

    with self.engine.connect() as con:
        con.execute("""
                          DELETE FROM tweet
                          WHERE created_at in(
                              SELECT created_at
                                  FROM(
                                      SELECT created_at, strftime('%s','now') - strftime('%s',created_at) AS time_passed
                                      From tweet
                                      WHERE time_passed >= 60))""")
