from brownie import Whipper, accounts
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

def main():
    acct = accounts.at(os.getenv("DEPLOY_ADDRESS"))
    whipper = Whipper.at(os.getenv("CONTRACT_MAINNET_ADDRESS"))
    whipper.setBreaker(False, {'from': acct})
