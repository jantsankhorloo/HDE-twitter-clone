from flask import flash
from redis import Redis
import config
import re

redis = Redis(host='localhost')

def hashtag_handler(text):
    hashtag_found = 0 #0 if no, 1 if yes
    hashtag_text = ""
    count = 0
    left_text = ""
    right_text = ""
    if "#" in text:	
        hashtag_found = 1
	for i in range(text.find("#") + 1, len(text)):
	    if text[i] == " ": break
    	    hashtag_text += text[i]
            count += 1
	for i in range(0, text.find("#")):
	    left_text += text[i]
	for i in range(len(left_text) + len(hashtag_text) + 1, len(text)):
	    right_text += text[i]
    return hashtag_found, hashtag_text, left_text, right_text

def hashtag_handler2(text):
    hashtags = re.findall(r'#\w*', text)
    regular_words = [each for each in text.split() if each not in hashtags and each[0] != "#"]
    #aiming to support more than 1 hashtag

def post_size_handler(text):
    if (len(text) > config.MAX_POST_LENGTH):
    	flash("Post should not exceed 140 characters")
    	return False
    if (len(text) == 0):
    	flash("Please type something. Cannot post empty string") 
    	return False
    return True

def create_tweet(tweet, each_id):
    return {
        'old_id': tweet['old_id'], #useful for referring back to the original post in hashtag html
        'id': each_id,             #each_id refers to each id in pool_ids 
        'text': tweet['text'].decode('utf-8'), 
        'user': redis.hget('users', tweet['user']).decode('utf-8'), #get the user full name 
        'googleid': tweet['user'],  #google id token, is also in session['user']
        'session_id': tweet['session_id'], #unique user id, google id -> SHA256 -> session_id, also in session['id']
        'time': int(str(tweet['time']).split(".")[0]), #split it by . and get the first part for js parsing in html

        'hashtag': int(tweet['hashtag']),       #0 if there is no hashtag in post, 1 if yes
        'hashtag_text': tweet['hashtag_text'].decode('utf-8'),  #parse out the hashtag value from the text
        'left_text': tweet['left_text'].decode('utf-8'),        #separate the left part of hashtag text for easy display in html
        'right_text': tweet['right_text'].decode('utf-8'),      #the right side as well

        'avatar': redis.hget('avatars', tweet['user']), #save google avatar pic url here
        'retweet': int(tweet['retweet']),               #1 if this tweet is someone's retweet, 0 if not
        'retweet_from': tweet['retweet_from'],          #the original tweet owner if it is a retweet
        'retweet_user_id': tweet['retweet_user_id']     #save the original tweet owner id for easy url linking in html
         }
