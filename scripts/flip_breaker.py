from brownie import Whipper, accounts
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

def main():
    acct = accounts.at(os.getenv("DEPLOY_ADDRESS"))
    whipper = Whipper.at(os.getenv("CONTRACT_MAINNET_ADDRESS"))
    print("whipper admin ", whipper.owner())
    print("deploy account ", acct)
    assert acct == whipper.owner()
    whipper.setBreaker(False, {'from': acct})
