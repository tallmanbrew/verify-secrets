if ! command -v jq > /dev/null
then
    echo "jq not installed, attempting to install"
    sudo apt update
    sudo apt install jq -y
else 
    echo "jq installed"
fi