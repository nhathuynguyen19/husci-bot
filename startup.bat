eval rm -rf Husci-Bot &&
git clone https://nhathuynguyen19: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@github.com/nhathuynguyen19/Husci-Bot.git && 
pip install -r Husci-Bot/requirements.txt &&
cd Husci-Bot &&
git config user.name "nhathuynguyen19" &&
git config user.email "huythcsthuyphuong73@gmail.com" &&
cd .. &&
python3 Husci-Bot/app.py