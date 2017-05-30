from flask import url_for, request
from oauth2client.client import flow_from_clientsecrets
from apiclient.discovery import build
import httplib2
import config

def new_flow():
    return flow_from_clientsecrets(config.CLIENT_SECRETS, 
				  scope='https://www.googleapis.com/auth/userinfo.profile',
				  redirect_uri= "http://localhost:5000/oauth2callback")

def flow1():
    flow = new_flow()
    auth_uri = flow.step1_get_authorize_url()
    return auth_uri


def flow2():
    flow = new_flow()
    credentials = flow.step2_exchange(request.args['code'])
    http_auth = credentials.authorize(httplib2.Http())
    profile = build('oauth2', 'v2', http=http_auth)
    user_info = profile.userinfo().get().execute()
    google_id, user_given_name, user_avatar = user_info['id'], user_info['name'], user_info['picture']
    return google_id, user_given_name, user_avatar
