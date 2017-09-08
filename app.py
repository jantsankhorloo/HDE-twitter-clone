#!/usr/bin/env python
# Libraries in Python
import hashlib
import config
import base64
import boto3
import time
import uuid
import os

# Secondary Libraries
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from oauth2client import client
from flask_oauth import OAuth
from redis import Redis

# Library written by me
from lib import s3, handler, google

redis = Redis(host='localhost')

app = Flask(__name__)
app.secret_key = hashlib.sha512(str(uuid.uuid4())).hexdigest()
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE

#global list containing all the tweet ids
pool_ids = []  

#global var used to list which users the profile is un/following
user_id_follow = ""
user_id_unfollow = ""

@app.route("/")
def index():
    if 'user' not in session:
	return render_template('signin.html')
    return redirect(url_for('home'))

@app.route("/login")
def login():
    #auth_uri = flow.step1_get_authorize_url()
    auth_uri = google.flow1()
    return redirect(auth_uri)

#redirection after google SSO
@app.route("/oauth2callback") 
def oauth2callback():
    google_id, user_given_name, user_avatar = google.flow2()
    print(google_id, user_given_name, user_avatar) 
    session['user'] = google_id

    session_id = hashlib.sha256(google_id.encode('utf-8')).hexdigest()
    session['id'] = session_id

    redis.hset('users_id', session_id, user_given_name.encode('utf-8'))
    redis.hset('avatars_id', session_id, user_avatar)

    #hset(self, name, key, value) - setting google_id as key and name as value in order to not have duplicate usernames
    redis.hset('users', google_id, user_given_name.encode('utf-8'))
    #user_avatar here is given a https url for the .jpg
    redis.hset('avatars', google_id, user_avatar)
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route("/home")
def home():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    tweets = []
    for each_id in pool_ids:
	tweet = redis.hgetall(each_id)
	new_tweet = handler.create_tweet(tweet, each_id)
    
	if "img" in tweet:
	    new_tweet["img"] = s3.s3_retrieve(tweet["img"])
	tweets.insert(0, new_tweet)
        
    current_user = session['id'].encode('utf-8')

    following = redis.smembers("f" + user_id_follow)
    googleid = session['user']
    session_id = session['id']
    username= redis.hget('users_id', session_id).decode('utf-8')
    
    return render_template('home.html', 
			tweets=tweets, 
			googleid=googleid,
			session_id=session_id, 
			username=username)

@app.route('/profile/<session_id>', methods=['GET'])
def profile(session_id):
    session_id = session_id.encode('utf-8')
    tweets = []

    for each_id in pool_ids:
    	tweet = redis.hgetall(each_id)
    	if tweet['session_id'] == session_id:
    	    new_tweet = handler.create_tweet(tweet, each_id)
    	    if "img" in tweet:
    	        new_tweet["img"] = s3.s3_retrieve(tweet["img"])

            tweets.insert(0, new_tweet)

    current_user = session['id'].encode('utf-8')
    following = redis.smembers("b" + current_user)
    following_names = []
    following_names_id = {}
    for each in following:
        name = redis.hget('users_id', each)
    	following_names.append(name)
    	following_names_id[name] = each

    follower = redis.smembers("f" + session_id)
    follow_names = []
    follow_names_id = {}
    for each in follower:
    	name = redis.hget('users_id', each)
    	follow_names.append(name)
    	follow_names_id[name] = each

    try:
        username = redis.hget('users_id', session_id).decode('utf-8')
    except AttributeError:
        flash("Invalid URL")
        return redirect(url_for("home"))
    avatar = redis.hget('avatars_id', session_id)
    viewing_user = session['id']
    user = redis.hget('users_id', viewing_user).decode('utf-8')
    return render_template('profile.html', 
    			   id=session['id'],#id of the user seeing the page 
    			   session_id= session_id,
    			   username=username, 
    			   user=user,
    			   tweets=tweets, 
    			   avatar=avatar,
    			   follower=follower,
    			   follow_names=follow_names,
    			   follow_names_id=follow_names_id,
    			   following_names=following_names,
    			   following_names_id=following_names_id)

@app.route('/hashtag/<tweet_id>', methods=['GET'])
def hashtag(tweet_id):
    hash_tweet = redis.hgetall(str(tweet_id))
    tweets = []
    for each_id in pool_ids:
	tweet = redis.hgetall(each_id)
	if hash_tweet['hashtag_text'] in tweet['hashtag_text']:
	    new_tweet = handler.create_tweet(tweet, each_id)
	    if "img" in tweet:
		new_tweet["img"] = s3.s3_retrieve(tweet["img"])

	    tweets.insert(0, new_tweet)
    session_id = session['id']
    username= redis.hget('users_id', session_id).decode('utf-8')
    return render_template('hashtag.html', 
			    tweets=tweets, 
	    		    hashtag=hash_tweet['hashtag_text'].decode('utf-8'), 
	       		    session_id=session['id'],
	       		    username=username,
                          tweet_id=tweet_id)

@app.route('/feed/<user_id>', methods=["GET"])
def feed(user_id):	
    try:
        valid_user = redis.hget('users_id', user_id).decode('utf-8')
    except AttributeError:
        flash("Invalid URL")
        return redirect(url_for('home'))
    current_user = session['id'].encode('utf-8')
    following = redis.smembers("b" + current_user)
    id_list = []
    for each in following:
        id_list.append(each)

    tweets = []
    for each_id in pool_ids:
	tweet = redis.hgetall(each_id)
	if tweet['session_id'] in id_list or tweet['session_id'] == current_user:
	    new_tweet = handler.create_tweet(tweet, each_id)
	    if "img" in tweet:
		new_tweet["img"] = s3.s3_retrieve(tweet["img"])

            tweets.insert(0, new_tweet)			
    session_id = session['id']
    username= redis.hget('users_id', session_id).decode('utf-8')
    return render_template('feed.html',
	                    tweets=tweets,
			    session_id=user_id,
			    username=username)

@app.route('/post/<page>/<user_id>', methods=['POST'])
def post(page, user_id):
    text = request.form['text']
    if (handler.post_size_handler(text) == False):
	if (page == "home"):
            return redirect(url_for('home'))
        elif (page == "feed"):
            return redirect(url_for('feed', user_id=user_id))
        return redirect(url_for('profile', session_id=user_id))

    hashtag, hashtag_text, left_text, right_text = handler.hashtag_handler(text)
    tweet_id = str(uuid.uuid4().hex)

    img = request.files['img']

    new_tweet = {
		'googleid': session['user'],
		'session_id': session['id'],
		'old_id': "",
		'id': tweet_id,
		'user': session['user'],
		'text': text.encode('utf-8'),
		'time': time.time(),
		'hashtag': hashtag,
		'hashtag_text': hashtag_text,
		'left_text': left_text,
		'right_text': right_text,
		'avatar':redis.hget('avatars', session['user']),
		'retweet': 0,
		'retweet_from': "",
		'retweet_user_id': ""
	        }
    
    if img and img.content_type.startswith("image/"): #if there is image
	fname = tweet_id + '-' + secure_filename(img.filename)
	s3.s3_upload(fname, img)
	new_tweet['img'] = fname
    elif img and not img.content_type.startswith("image/"):
        flash("Invalid image type!")
        if (page == "home"):
            return redirect(url_for('home'))
        elif (page == "feed"):
            return redirect(url_for('feed', user_id=user_id))
        return redirect(url_for('profile', session_id=user_id))


    pool_ids.append(tweet_id)
    redis.hmset(tweet_id, new_tweet)

    if (page == "home"):
    	return redirect(url_for('home'))
    elif (page == "feed"):
    	return redirect(url_for('feed', user_id=user_id))
    return redirect(url_for('profile', session_id=user_id))

@app.route('/edit/<tweet_id>', methods=['GET', 'POST'])
def edit(tweet_id):
    page = tweet_id[:4]
    tweet_id = tweet_id[4:]
    tweet = redis.hgetall(str(tweet_id))
    text = request.form['text']

    if (handler.post_size_handler(text) == False):
        if (page == "home"):
            return redirect(url_for('home'))
        elif (page == "feed"):
            return redirect(url_for('feed', user_id=tweet['session_id']))
        return redirect(url_for('profile', session_id=session['id']))

    tweet['text'] = text

    hashtag, hashtag_text, left_text, right_text = handler.hashtag_handler(text)
    
    tweet['hashtag'] = hashtag
    tweet['hashtag_text'] = hashtag_text
    tweet['left_text'] = left_text
    tweet['right_text'] = right_text

    img = request.files['img']
    
    if img and img.content_type.startswith("image/"): #if there is image
	fname = tweet_id + '-' + secure_filename(img.filename)
    	s3.s3_upload(fname, img)
	tweet['img'] = fname

    redis.hmset(tweet_id, tweet)
    if (page == "home"):
    	return redirect(url_for('home'))
    elif (page == "feed"):
    	return redirect(url_for('feed', user_id=tweet['session_id']))
    return redirect(url_for('profile', session_id=session['id']))
		
@app.route('/delete/<tweet_id>', methods=['GET'])
def delete(tweet_id):
    page = tweet_id[:4]
    tweet_id = tweet_id[4:]
    pool_ids.remove(tweet_id)
    redis.delete(tweet_id)
    
    if (page == "home"):
    	return redirect(url_for('home'))
    elif (page == "feed"):
    	return redirect(url_for('feed', user_id=session['id']))
    return redirect(url_for('profile', session_id=session['id']))

@app.route('/followprofile/<user_id>', methods=['GET'])
def followprofile(user_id):#googleid of the person being followed
    current_user = session['id'].encode('utf-8')
    user_id = user_id.encode('utf-8')
    user_id_follow = user_id#being followed

    following = redis.smembers("f" + user_id_follow)

    if (current_user in following):
	flash("You are already following this profile.")
	return redirect(url_for('profile', session_id=user_id_follow))

    if (current_user != user_id):
	redis.sadd("f" + user_id_follow, current_user)#following  -- currentuser follows user_id
	redis.sadd("b" + current_user, user_id)#followedby. -- user_id is being followed by current_user

    flash("You are now following this profile.")
    return redirect(url_for('profile', session_id=user_id_follow))

@app.route('/unfollowprofile/<user_id>', methods=['GET'])
def unfollowprofile(user_id):
    current_user = session['id'].encode('utf-8')
	
    user_id = user_id.encode('utf-8')
    user_id_unfollow = user_id#being unfollowed

    following = redis.smembers("f" + user_id_unfollow)
    if (current_user not in following):
	flash("You DO NOT follow this user already.")
	return redirect(url_for('profile', session_id=user_id_unfollow))

    redis.srem("f" + user_id_unfollow, current_user)
    redis.srem("b" + current_user, user_id)
    flash("You are now UNFOLLOWING this user.")
    return redirect(url_for('profile', session_id=user_id_unfollow))


@app.route('/retweet/<tweet_id>', methods=['GET', 'POST'])
def retweet(tweet_id):
    page = tweet_id[:4]
    tweet = redis.hgetall(str(tweet_id[4:]))

    retweeting_owner= tweet['user']
    retweeting_from = redis.hget('users', retweeting_owner).decode('utf-8')
	
    new_tweet_id = str(uuid.uuid4().hex)
    tweet['old_id'] = tweet['id']
    tweet['id'] = new_tweet_id
    tweet['user'] = session['user']
    tweet['retweet_user_id'] = tweet['session_id']
    tweet['session_id'] = session['id']
    tweet['time'] = time.time()
    tweet['retweet'] = 1
    tweet['avatar'] = redis.hget('avatars', session['user'])
    tweet['retweet_from'] = retweeting_from

    pool_ids.append(new_tweet_id)
    redis.hmset(new_tweet_id, tweet)
        
    if (page == "home"):     
        return redirect(url_for('home'))
    elif (page == "feed"):
        return redirect(url_for('feed', user_id=session['id']))
    return redirect(url_for('profile', session_id=session['id']))

@app.route('/original_retweet/<tweet_id>', methods=['GET'])
def original_retweet(tweet_id):
    page = tweet_id[:4]
    tweet_id = tweet_id[4:]
    if tweet_id not in pool_ids:
        flash("The tweet does not exit.")
        if (page == "home"):     
    	    return redirect(url_for('home'))
        elif (page == "feed"):
	    return redirect(url_for('feed', user_id=session['id']))
	return redirect(url_for('profile', session_id=session['id']))

    tweet = redis.hgetall(str(tweet_id))
    if "img" in tweet:
        tweet["img"] = s3.s3_retrieve(tweet["img"])
    
    session_id = session['id']
    tweet['hashtag_text'] = tweet['hashtag_text'].decode('utf-8')
    tweet['left_text'] = tweet['left_text'].decode('utf-8')
    tweet['right_text'] = tweet['right_text'].decode('utf-8')
    username= redis.hget('users_id', tweet['session_id']).decode('utf-8')
    current_user = redis.hget('users_id', session_id).decode('utf-8')

    return render_template('original_retweet.html', 
                            tweet=tweet, 
                            session_id=session_id,
			    username=username, 
                            current_user=current_user)

if __name__ == '__main__':
    app.run(debug=True)
