# noss-mint-script
noss auto mint scirpt.

### 🛫 All you need is to change your own private key.
`private_key = "type_your_private_key_here"`

## Step1 install package
run below command in terminal  
`pip install --use-pep517 -r requirements.txt`  

如果你在境内请使用以下命令  
`pip install --use-pep517 -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### ‼️ If you use windows, you can fllow the steps below  
`pip install -r requirements_in_win.txt`  
如果你在境内请使用以下命令    
`pip install -r requirements_in_win.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`


# Step2 change your private key
change your private key in `noss_mint.py` file, just like below  
in line 293  
`private_key = "type_your_private_key_here"`
 ->  
`private_key = "nsec1fn0vvudj4uz4wuu2jm9kpa4xhdydruee9f7tapj980ejncfte6ustyrd70"`
### ⚠️ I just use a random private key here, you should use your own private key.

## Step3 run script    
run below command in terminal  
`python3 noss_auto_sign.py`
### if you use windows, you can run below command
`python noss_auto_sign_in_win.py`

### Options u guys also can change the theread number
just change the `thread_num` in `noss_auto_sign.py` file, just like below  
in line 299   
`thread_num = 10`

## By the way, if you want to generate multiple private keys, you can use the following command
`python3 generate_multi_key.py`
