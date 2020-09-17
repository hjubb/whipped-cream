import pytest
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from brownie import *

@pytest.fixture
def me():
    return a.at(os.getenv("TEST_ADDRESS"))


@pytest.fixture
def whipper(me):
    return me.deploy(Whipper)


def test_lifecycle(whipper, me, pm):
    print("finding tokens...")
    staking_rewards_lock = interface.StakingRewardsLock(whipper.creamPool())
    ieip20 = pm("compound-finance/compound-protocol@2.8.1").CErc20
    cream = ieip20.at(whipper.cream())
    cream_starting_bal = cream.balanceOf(me)
    w_cream = ieip20.at(whipper.wCream())
    print("found tokens")

    print("approving cream token for spend in whipper")
    approve_token(cream, me, whipper)

    # how many I have now
    assert w_cream.balanceOf(me) == 0

    print("depositing cream token bal into whipper")
    whipper.depositAll({'from': me})
    assert cream.balanceOf(me) == 0
    w_cream_bal = w_cream.balanceOf(me)
    assert w_cream_bal > 0
    print("rewards should be 0")
    assert staking_rewards_lock.earned(whipper) == 0

    # get some rewards cooking
    chain.mine(3)

    print("rewards should be > 0")
    assert staking_rewards_lock.earned(whipper) > 0

    whipper.whip({'from': me})
    print("I should have cream as caller of whip")
    my_new_bal = cream.balanceOf(me)
    assert my_new_bal > 0

    print("contract shouldn't have any cream left after whip")
    assert cream.balanceOf(whipper) == 0
    print("assert balances don't change on whipping, only underlying cream value")
    assert w_cream.balanceOf(me) == w_cream_bal
    approve_token(w_cream, me, whipper)
    whipper.withdrawAll({'from': me})
    print("my withdrawn creambal should be greater than starting, after whipping")
    assert cream.balanceOf(me) > cream_starting_bal + my_new_bal



def approve_token(token, me, spender):
    token.approve(spender, token.balanceOf(me), {'from': me})
