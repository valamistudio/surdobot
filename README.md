## Introduction
This is a lightweight voice transcription bot for telegram. It runs Python 3 in a serverless AWS Lambda instance through [Chalice](https://github.com/aws/chalice) using [FFMpeg](https://ffmpeg.org/), [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/) and [Wit.AI](https://wit.ai/).

## Running
```sh
mkdir ~/.aws
$ cat >> ~/.aws/config
[default]
aws_access_key_id=YOUR_ACCESS_KEY_HERE
aws_secret_access_key=YOUR_SECRET_ACCESS_KEY
region=YOUR_REGION (such as us-west-2, us-west-1, etc)

mkdir surdobot
cd surdobot
python -m venv venv
source venv/scripts/activate
git clone https://github.com/valamistudio/surdobot.git
cd surdobot/src
pip install -r requirements.txt
chalice deploy

curl -X "POST" "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" -d '{"url": "<REST_API_URL>/webhook"}' -H 'Content-Type: application/json; charset=utf-8'
```

## `src/.chalice/config.json`
```json
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
        "wit_token": "<YOUR_WIT_TOKEN>"
      }
    }
  }
}
```

### Useful links
- [Telegram BotFather](https://t.me/BotFather)
- [Wit.AI](https://wit.ai/)
- [FFMPEG Lambda Layer](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:145266761615:applications~ffmpeg-lambda-layer)
