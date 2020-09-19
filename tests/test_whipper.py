import pytest
import os
from dotenv import load_dotenv, find_dotenv
from math import isclose
load_dotenv(find_dotenv())

from brownie import *

@pytest.fixture
def me():
    return a.at(os.getenv("TEST_ADDRESS"))


@pytest.fixture
def other():
    return a[0] # some random account given with ganache-cli


@pytest.fixture
def whipper(me):
    return me.deploy(Whipper)


def test_lifecycle(whipper, me, pm):
    print("finding tokens...")
    staking_rewards_lock, cream, w_cream = get_tokens(whipper, pm)
    cream_starting_bal = cream.balanceOf(me)
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


def test_balances(whipper, me, other, pm):
    _, cream, w_cream = get_tokens(whipper, pm)
    approve_token(cream, me, whipper)

    my_balance = cream.balanceOf(me)
    to_send = my_balance / 3

    print("my_balance is ", my_balance)
    print("to_send is ", to_send)

    cream.transfer(other, to_send, {'from': me})

    my_balance = cream.balanceOf(me)
    user_ratio = my_balance / to_send

    approve_token(cream, other, whipper)

    whipper.depositAll({'from': me})
    whipper.depositAll({'from': other})

    assert isclose(w_cream.balanceOf(me), w_cream.balanceOf(other) * user_ratio, rel_tol=0.00001)


def approve_token(token, me, spender):
    token.approve(spender, token.balanceOf(me), {'from': me})


def get_tokens(whipper, pm):
    staking_rewards_lock = interface.StakingRewardsLock(whipper.creamPool())
    ieip20 = pm("compound-finance/compound-protocol@2.8.1").CErc20
    cream = ieip20.at(whipper.cream())
    w_cream = ieip20.at(whipper.wCream())
    return staking_rewards_lock, cream, w_cream
