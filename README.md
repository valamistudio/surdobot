![GitHub](https://img.shields.io/github/license/valamistudio/surdobot?style=flat-square)
![Libraries.io dependency status for GitHub repo](https://img.shields.io/librariesio/github/valamistudio/surdobot?style=flat-square)

## Introduction
This is a lightweight voice transcription bot for telegram. It runs Python 3 in a serverless AWS Lambda instance through [Chalice](https://github.com/aws/chalice) using [FFMpeg](https://ffmpeg.org/), [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/) and [Wit.AI](https://wit.ai/).

## Running
```sh
mkdir ~/.aws
cat >> ~/.aws/config <<EOF
[default]
aws_access_key_id=<YOUR_ACCESS_KEY>
aws_secret_access_key=<YOUR_SECRET_KEY>
region=<YOUR_REGION> (such as us-west-2, us-west-1, etc)
EOF
git clone https://github.com/valamistudio/surdobot.git
cd surdobot/src
mkdir .chalice
cat >> .chalice/config.json <<EOF
{
  "version": "2.0",
  "app_name": "surdobot",
  "automatic_layer": true,
  "layers": ["<YOUR_FFMPEG_LAYER>"],
  "stages": {
    "dev": {
      "api_gateway_stage": "api",
      "environment_variables": {
        "bot_token": "<YOUR_BOT_TOKEN>",
        "wit_token": "<YOUR_WIT_TOKEN>",
        "user_ids": "<OPTIONAL_USER_ID_COMMA_SEPARATED_WHITELIST>"
      }
    }
  }
}
EOF
python -m pip install pipenv
python -m pipenv install
python -m pipenv shell
chalice deploy

curl -X "POST" "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" -d '{"url": "<REST_API_URL>/webhook"}' -H 'Content-Type: application/json; charset=utf-8'
```
The REST API URL comes from the `chalice deploy` command output, so you'll probably want to execute that last command in separate.
On `.chalice/config.json`, if `user_ids` is assigned, the bot will only respond to private chat of users in the whitelist or to groups/supergroups/channels of which any user of the whitelist is a member. Otherwise, the bot will apply no restrictions.

### Useful links
- [Telegram BotFather](https://t.me/BotFather)
- [Wit.AI](https://wit.ai/)
- [FFMPEG Lambda Layer](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:145266761615:applications~ffmpeg-lambda-layer)
