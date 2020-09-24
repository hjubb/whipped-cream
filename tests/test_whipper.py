import pytest
import os
from dotenv import load_dotenv, find_dotenv
from math import isclose
load_dotenv(find_dotenv())

from brownie import *
import brownie

@pytest.fixture
def me():
    yield accounts.at(os.getenv("TEST_ADDRESS"))


@pytest.fixture
def other():
    yield accounts[0]  # some random account given with ganache-cli


@pytest.fixture()
def owner():
    yield accounts.at(os.getenv("OWNER_ADDRESS"))


@pytest.fixture
def cream_owner():
    yield accounts.at(os.getenv("CREAM_DEPLOYER_ADDRESS"))


@pytest.fixture(scope="function", autouse=True)
def whipper(owner):
    yield Whipper.deploy(os.getenv("DEPLOYED_CREAM_POOL"), {'from': owner})


def test_lifecycle(whipper, me, pm, cream_owner):
    chain.snapshot()
    print("finding tokens...")
    staking_rewards_lock, cream, w_cream = get_tokens(whipper, pm)
    staking_rewards_lock.setBreaker(True, {'from': cream_owner})
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
    chain.mine(1)

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
    chain.revert()


def test_balances(whipper, me, other, pm, cream_owner):
    chain.snapshot()
    staking_rewards_lock, cream, w_cream = get_tokens(whipper, pm)
    staking_rewards_lock.setBreaker(True, {'from': cream_owner})
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
    approve_token(w_cream, me, whipper)
    approve_token(w_cream, other, whipper)
    whipper.withdrawAll({'from': me})
    whipper.withdrawAll({'from': other})
    chain.revert()


def test_migrations(whipper, me, other, pm, cream_owner, owner):
    chain.snapshot()
    staking_rewards_lock, cream, w_cream = get_tokens(whipper, pm)
    staking_rewards_lock.setBreaker(True, {'from': cream_owner})
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

    whipper.migratePool(os.getenv("MIGRATION_CREAM_POOL"), {'from': owner})

    approve_token(w_cream, me, whipper)
    approve_token(w_cream, other, whipper)
    whipper.withdrawAll({'from': me})
    whipper.withdrawAll({'from': other})

    assert cream.balanceOf(me) > my_balance

    chain.revert()


def test_other_user_migrate(whipper, me, pm, cream_owner):
    chain.snapshot()
    staking_rewards_lock, cream, w_cream = get_tokens(whipper, pm)
    staking_rewards_lock.setBreaker(True, {'from': cream_owner})
    approve_token(cream, me, whipper)

    whipper.depositAll({'from': me})

    with brownie.reverts("Sender not authorized."):
        whipper.migratePool(os.getenv("MIGRATION_CREAM_POOL"), {'from': me})

    approve_token(w_cream, me, whipper)
    whipper.withdrawAll({'from': me})
    chain.revert()


def approve_token(token, me, spender):
    token.approve(spender, token.balanceOf(me), {'from': me})


def get_tokens(whipper, pm):
    staking_rewards_lock = interface.StakingRewardsLock(whipper.creamPool())
    ieip20 = pm("compound-finance/compound-protocol@2.8.1").CErc20
    cream = ieip20.at(whipper.cream())
    w_cream = ieip20.at(whipper.wCream())
    return staking_rewards_lock, cream, w_cream
