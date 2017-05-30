import sys 
sys.path.insert(0, '..')
from lib import s3, handler, google
from redis import Redis 
from mock import Mock

from StringIO import StringIO
import flask
import config
import unittest
import logging
import app

config.CLIENT_SECRETS = '../client_secrets.json'

class TestCase():

	def setup(self):
	    app.app.config['TESTING'] = True
	    self.app = app.app.test_client()
	    app.redis = Redis()
	    #app.redis.flushdb()
	    s3.s3_upload = Mock()
	    s3.s3_retrieve = Mock(return_value="thisisbase64data")
	    google.flow2 = Mock(return_value = ('113370958690178099498', 
                                                'Jantsankhorloo Amgalan',
	    'https://lh6.googleusercontent.com/-huTFrJVI_yM/AAAAAAAAAAI/AAAAAAAAAKU/h7XgrR9dyc8/photo.jpg'))

	def login(self):
	    return self.app.get('/oauth2callback?code=4')

	def logout(self):
	    return self.app.get('/logout', follow_redirects=True)

	def test_index(self):
	    rv = self.app.get('/')
	    assert 'Login with' in rv.data

	def test_home(self):#index page
	    self.login()
	    rv = self.app.get('/', follow_redirects=True)
	    assert 'Global Timeline' in rv.data

	def test_oauth_redirect(self):
	    rv = self.app.get('/login')
	    assert rv.status_code == 302
	    assert 'accounts.google.com' in rv.location	
        
        def test_logout(self):
	    self.login()
	    rv = self.logout() 
            assert 'Login with' in rv.data

        def test_home2(self):#without signin
            rv = self.app.get('/home', follow_redirects=True)
            assert 'Login with' in rv.data

        def test_home3(self):#with sigin
            self.login()
            rv = self.app.get('/home')
            assert "Global Timeline" in rv.data

        def test_post_tweet_0(self):#no characters
            self.login()
            rv = self.app.post('/post/home/0', 
                                data=dict(text = ""), 
                                follow_redirects=True, 
                                content_type="multipart/form-data")
            assert "Please type something. Cannot post empty string" in rv.data

        def test_post_tweet_141(self):
            self.login()
            rv = self.app.post('/post/home/0',
                               data=dict(text=("#solong#solong#solong"
                                               "#solong#solong#solong"
                                               "#solong#solong#solong"
                                               "#solong#solong#solong"
                                               "#solong#solong#solong"
                                               "#solong#solong#solong"
                                               "#solong#solong#")),
                               follow_redirects=True,
                               content_type="multipart/form-data")
            assert "Post should not exceed 140 characters" in rv.data

        def test_post_invalid_img(self):
            self.login()
            rv = self.app.post('/post/home/0', data=dict(
                text="Test",
                img=(open('../config.py', 'rb'), 'config.py')),
                follow_redirects=True, 
                content_type="multipart/form-data")
            assert "Invalid image type!" in rv.data
            assert "thisisbase64data" not in rv.data

        def test_post_tweet_noimg(self):
            self.login()
            rv = self.app.post('/post/home/0', 
                                data=dict(text = "Test",
                                img=(StringIO(''), '')), #File-like object 
                                follow_redirects=True, 
                                content_type="multipart/form-data")
            assert "Test" in rv.data
            assert "<p><img" not in rv.data
            assert "thisisbase64data" not in rv.data

        def test_post_tweet_img(self):
            self.login()
            rv = self.app.post('/post/home/0', data=dict(
                text="Test",
                img=(open("sample.png", "rb"), "sample.png")),
                follow_redirects=True,
                content_type="multipart/form-data")
            assert "Test" in rv.data
            assert "<p><img" in rv.data
            assert "thisisbase64data" in rv.data 
    
        def test_post_hashtag(self):
            self.login()
            rv = self.app.post('/post/home/0', 
                                data=dict(text = "#Test",
                                img=(StringIO(''), '')), #File-like object 
                                follow_redirects=True, 
                                content_type="multipart/form-data")
            assert "#" in rv.data

        def test_post_tweet_gif(self):#large file 2.1 mb
            self.login()
            rv = self.app.post('/post/home/0', data=dict(
                text="Test",
                img=(open("sample.gif", "rb"), "sample.gif")),
                follow_redirects=True,
                content_type="multipart/form-data")
            assert "Test" in rv.data
            assert "<p><img" in rv.data
            assert "thisisbase64data" in rv.data 
        
        def test_post_notext_img(self):
            self.login()
            rv = self.app.post('/post/home/0', data=dict(
                text="",
                img=(open("sample.gif", "rb"), "sample.gif")),
                follow_redirects=True,
                content_type="multipart/form-data")
            assert "Please type something. Cannot post empty string" in rv.data
    
        def test_profile(self):#with signin
            self.login()
            id_token = ""
            with self.app as c:
                with c.session_transaction() as sess:
                    id_token = sess['id']
            
            rv = self.app.get('/profile/' + id_token)
            assert "Jantsankhorloo Amgalan" in rv.data

        def test_post_text_profile_noimg(self):
            self.login()
            id_token = ""
            with self.app as c:
                with c.session_transaction() as sess:
                    id_token = sess['id']

            rv = self.app.post('/post/prof/' + id_token, data=dict(
                    text="Test Profile", img=(StringIO(''), '')),
                    follow_redirects=True, content_type="multipart/form-data")
            assert "Test Profile" in rv.data
            assert "Profile Timeline" in rv.data

        def test_post_text_profile_img(self):
            self.login()
            id_token = ""
            with self.app as c:
                with c.session_transaction() as sess:
                    id_token = sess['id']

            rv = self.app.post('/post/prof/' + id_token, data=dict(
                    text="Test Profile", img=(open('sample.png', 'rb'), 'sample.png')),
                    follow_redirects=True, content_type="multipart/form-data")
            
            assert "Test Profile" in rv.data
            assert "Jantsankhorloo Amgalan" in rv.data
            assert "<p><img" in rv.data 
            assert "thisisbase64data" in rv.data

        def test_feed(self):#with signin
            self.login()
            id_token = ""
            with self.app as c:
                with c.session_transaction() as sess:
                    id_token = sess['id']
            
            rv = self.app.get('/feed/' + id_token)
            assert "Feed" in rv.data

        def test_post_text_feed_noimg(self):
            self.login()
            id_token = ""
            with self.app as c:
                with c.session_transaction() as sess:
                    id_token = sess['id']

            rv = self.app.post('/post/feed/' + id_token, data=dict(
                    text="Test Feed", img=(StringIO(''), '')),
                    follow_redirects=True, content_type="multipart/form-data")
            assert "Test Feed" in rv.data
        
        def test_post_text_feed_img(self):
            self.login()
            id_token = ""
            with self.app as c:
                with c.session_transaction() as sess:
                    id_token = sess['id']

            rv = self.app.post('/post/feed/' + id_token, data=dict(
                    text="Test Feed", img=(open('sample.png', 'rb'), 'sample.png')),
                    follow_redirects=True, content_type="multipart/form-data")
            
            assert "Test Feed" in rv.data
            assert "Jantsankhorloo Amgalan" in rv.data
            assert "<p><img" in rv.data 
            assert "thisisbase64data" in rv.data
