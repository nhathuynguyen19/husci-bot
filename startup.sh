#!/bin/bash
cd husci-bot-data
git config --local user.name "nhathuynguyen19"
git config --local user.email "huythcsthuyphuong73@gmail.com"
mv data ..
cd ..
mv data husci-bot/
pip install -r husci-bot/requirements.txt
cd husci-bot
chmod +x app.py
cd ..
python3 husci-bot/app.py