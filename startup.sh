@echo off
pip install -r Husci-Bot/requirements.txt
cd Husci-Bot
git config user.name "nhathuynguyen19"
git config user.email "huythcsthuyphuong73@gmail.com"
cd ..
python3 Husci-Bot/app.py
pause