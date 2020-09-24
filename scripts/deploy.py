from brownie import Whipper, accounts
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

def main():
    acct = accounts.at(os.getenv("DEPLOY_ADDRESS"))
    print("deployer account is ", acct)
    Whipper.deploy(os.getenv("DEPLOYED_CREAM_POOL"), {'from': acct})
