#!/bin/bash

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

echo "Please note that installing THREAT/crawl from binary must be considered for test purposes only and not for production use! The .deb file will contain (!) default credentials (!) to connect to the MongoDB instance, as specified in README.md."
if confirm("Are you sure you want to continue?") ; then
    sudo apt update && sudo apt upgrade -y
    sudo apt install python3.10 python3-tk python3-dev python3-pip npm git curl torbrowser-launcher xsel git wget curl unzip dpkg fakeroot xvfb xfce4-terminal -y
    sudo dpkg -i threatcrawl.deb

    VERSION=$(wget -O - https://github.com/mozilla/geckodriver | grep Latest -B 1 | grep "0\." | awk -F\> '{print $2}' | awk -F\< '{print $1}')
    wget "https://github.com/mozilla/geckodriver/releases/download/v$VERSION/geckodriver-v$VERSION-linux64.tar.gz" 2>/dev/null
    tar -xf "geckodriver-v$VERSION-linux64.tar.gz" 2>/dev/null
    sudo mv geckodriver /usr/local/bin/geckodriver

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
fi
