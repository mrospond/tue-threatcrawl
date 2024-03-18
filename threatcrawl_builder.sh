#!/bin/bash

REMOTE_INSTANCE="ssh -f -N -L 27017:localhost:27017 USERNAME@REMOTE_DB_HOST"
CURR_DIR=$(pwd)

confirm() {
    # call with a prompt string or use a default
    read -r -p "${1:- [y/N]} " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            true
            ;;
        *)
            false
            ;;
    esac
}

sudo apt update && sudo apt upgrade -y
sudo apt install python3.10 python3-tk python3-dev python3-pip npm git curl torbrowser-launcher xsel git wget curl unzip dpkg fakeroot xvfb xfce4-terminal -y
cd threatcrawl
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash
source ~/.bashrc
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
nvm install 16.13.0
# npm install --legacy-peer-deps
npm run make
cd out/THREATcrawl-linux-x64/resources/python
# python3.9 -m pip install -r requirements.txt
python3.10 -m pip install -r requirements.txt

echo -e "____________________________________\n"
echo -e "____________________________________\n"

echo "Installing geckodriver for Linux x64. If THREATcrawl raises an error about geckodriver, please check that the version installed matches your OS and that it's in the PATH."
VERSION=$(wget -O - https://github.com/mozilla/geckodriver | grep Latest -B 1 | grep "0\." | awk -F\> '{print $2}' | awk -F\< '{print $1}')
wget "https://github.com/mozilla/geckodriver/releases/download/v$VERSION/geckodriver-v$VERSION-linux64.tar.gz" 2>/dev/null
tar -xf "geckodriver-v$VERSION-linux64.tar.gz" 2>/dev/null
sudo mv geckodriver /usr/local/bin/geckodriver
echo -e "____________________________________\n"

echo -e "Remember that to run THREAT/crawl you need to execute the following:\n$REMOTE_INSTANCE\n"
echo -n "Please run TorBrowser Launcher once, and proceed to install TorBrowser in the system."
echo -e "____________________________________\n"

read -p "Once done, press enter to continue..."
mkdir -p ~/.local/share/torbrowser/tbb/x86_64/tor-browser_en-US/Browser/Downloads
cd $CURR_DIR
unzip Browser.zip -d ~/.local/share/torbrowser/tbb/x86_64/tor-browser_en-US/Browser/TorBrowser/Data

echo "If you failed to install TorBrowser properly, you have to execute these two commands from the terminal:"
echo "mkdir ~/.local/share/torbrowser/tbb/x86_64/tor-browser_en-US/Browser/Downloads"
echo "unzip Browser.zip -d ~/.local/share/torbrowser/tbb/x86_64/tor-browser_en-US/Browser/TorBrowser/Data"

echo -e "____________________________________\n"

echo "If there were no errors, congratulations! You will find the THREATcrawl executable in $CURR_DIR/threatcrawl/out/THREATcrawl-linux-x64/THREATcrawl"
echo "To install THREATcrawl in the system, you can run sudo dpkg -i $CURR_DIR/threatcrawl/out/make/deb/x64/threatcrawl_1.0.0_amd64.deb"
