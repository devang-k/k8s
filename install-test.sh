sudo apt update -y
sudo add-apt-repository ppa:deadsnakes/ppa -y 
sudo apt install python3.9 -y
sudo apt-get install python3.9-venv -y
rm -rf stagEnv/
python3.9 -m venv stagEnv
source stagEnv/bin/activate
python -V
python -m pip install -r requirements.txt
