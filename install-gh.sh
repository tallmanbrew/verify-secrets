if command -v gh > /dev/null
then
    echo "GitHub CLI not installed, attempting to install"
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key C99B11DEB97541F0
    sudo apt-add-repository https://cli.github.com/packages
    sudo apt update
    sudo apt install gh -y
else 
    echo "GitHub CLI installed"
fi