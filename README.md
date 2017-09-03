# jay-twitter-clone: WITTER - post something witty~

This project is a learning project when I was a software engineering intern at HDE, Inc Tokyo, Japan.

[HDE, Inc](https://www.hde.co.jp/en/) is a Japanese B2B cloud security company with over 74% market share. I was an intern in their Cloud Research Product Development team.

[Here](https://medium.com/@hdeglobalintern/jay-intern-life-and-6-weeks-in-tokyo-c3d2fdf9a6de) is a blog post I wrote about my internship and stay in Tokyo, Japan. It is posted on the company's Medium blogging website.

## Twitter Clone Objectives:

- dont change user from nginx in /etc/nginx/nginx.conf

## Twitter Clone Summary

### Features:
- Posting, Editing, Deleting, and Image Uploading using S3/Boto3
- Following and Unfollowing
- Follow only timeline, profile page, and global witter timeline which shows every user's post
- Handles hashtag only after the user posts it. There is html to show hashtagged posts, regardless of followage
- Google OpenID SSO
- Post size is 140 characters and empty post is not permitted
- Used Redis for storage
- Flask framework
- Deployed on AWS/EC2: jay.aws.prd.demodesu.com
- Unit testing on signing in and out, posting texts and images on home, profile and feed
- Enabled HTTPS with gninx/gunicorn as web server
