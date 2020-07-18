
# Install virtual environment
py -m pip install --user virtualenv

# Set up virtual environment
py -m venv env
source ./env/Scripts/activate

# Install all requirements
pip install -r requirements.txt

# Pytorch is a bitch, so we have to install it separately
pip install torch===1.5.1 torchvision===0.6.1 -f https://download.pytorch.org/whl/torch_stable.html