eval git clone --depth 1 https://github.com/nhathuynguyen19/Husci-Bot.git && 
mv Husci-Bot/* Husci-Bot/.* ./ 2>/dev/null && 
find Husci-Bot/ -mindepth 1 -exec mv {} ./ \; && 
rm -rf Husci-Bot && 
pip install -r requirements.txt && 
python3 app.py