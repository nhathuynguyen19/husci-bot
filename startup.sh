#!/bin/bash
cd Husci-Bot-Data
mv data ..
cd ..
mv data Husci-Bot/
pip install -r Husci-Bot/requirements.txt
cd Husci-Bot
chmod +x app.py
cd ..
cd Husci-Bot-Data
git config --local user.name "nhathuynguyen19"
git config --local user.email "huythcsthuyphuong73@gmail.com"
cd ..
python3 Husci-Bot/app.py