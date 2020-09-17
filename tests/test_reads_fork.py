import pytest
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from brownie import *

@pytest.fixture
def me():
    return accounts.at(os.getenv("TEST_ADDRESS"))

@pytest.fixture
def whipper(me):
    return me.deploy(Whipper)

def test_thing(whipper, me, pm):
    crCreamToken = pm("compound-finance/compound-protocol@2.8.1").CErc20Delegator
    crCream = crCreamToken.at(whipper.crCream())
    print(crCream.balanceOf(me))

    assert False
