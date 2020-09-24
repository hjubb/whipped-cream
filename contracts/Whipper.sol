pragma solidity ^0.5.16;

import "../interfaces/StakingRewardsLock.sol";
import "./DS.sol";
import "compound-finance/compound-protocol@2.8.1/contracts/CErc20Delegator.sol";
import "openzeppelin/openzeppelin-contracts@2.5.0/contracts/token/ERC20/IERC20.sol";
import "openzeppelin/openzeppelin-contracts@2.5.0/contracts/math/SafeMath.sol";
import "openzeppelin/openzeppelin-contracts@2.5.0/contracts/utils/ReentrancyGuard.sol";

contract Whipper is ReentrancyGuard {

    using SafeMath for uint256;

    constructor(address _creamPoolAddress) public {
        owner = msg.sender;
        creamPool = StakingRewardsLock(_creamPoolAddress);
        wCream = new DSToken("wCream");
        wCream.setName("Whipped Cream");
    }

    // Tokens
    address constant CREAM = 0x2ba592F78dB6436527729929AAf6c908497cB200;
    address constant CR_CREAM = 0x892B14321a4FCba80669aE30Bd0cd99a7ECF6aC0;

    IERC20 public cream = IERC20(0x2ba592F78dB6436527729929AAf6c908497cB200);
    CErc20Delegator public crCream = CErc20Delegator(0x892B14321a4FCba80669aE30Bd0cd99a7ECF6aC0);

    StakingRewardsLock public creamPool;

    // Last harvest
    uint256 public lastHarvest = 0;

    address public owner;
    bool public breaker = true;

    DSToken public wCream;

    function setBreaker(bool _breaker) public onlyOwner {
        breaker = _breaker;
    }

    function whip() public nonReentrant {
        // prevent people from burning gas if multiple harvests are submitted within short period of time
        if (lastHarvest > 0) {
            require(lastHarvest + 20 minutes <= block.timestamp, "!harvest-time or harvest debounced");
        }
        lastHarvest = block.timestamp;

        // collect cream
        creamPool.getReward();

        uint256 amount = cream.balanceOf(address(this));
        // NO DEV FEE SKIN IN THE GAME MOMENT
        // 5% perhaps and so on
        uint256 reward = amount.mul(5).div(100);

        // Sends 5% fee to caller
        cream.transfer(msg.sender, reward);

        // Remove amount from rewards
        amount = amount.sub(reward);

        _creamToCr(amount);

        // Deposit into masterchef contract
        uint256 balance = crCream.balanceOf(address(this));
        crCream.approve(address(creamPool),balance);
        creamPool.stake(balance);
    }

    function migratePool(address _newPool) public onlyOwner canWithdraw requireRewardsEnded nonReentrant {
        // pull out all funds (if possible)
        // collect all rewards
        creamPool.exit();
        // set new creamPool
        creamPool = StakingRewardsLock(_newPool);
        // send the regular whip 5% fee to admin, covering gas costs of the migration
        uint256 amount = cream.balanceOf(address(this));
        uint256 reward = amount.mul(5).div(100);
        cream.transfer(owner, reward);
        // deposit all assets again, maintaining user wCream ratio
        _creamToCr(cream.balanceOf(address(this)));
        uint256 balance = crCream.balanceOf(address(this));
        crCream.approve(address(creamPool),balance);
        creamPool.stake(crCream.balanceOf(address(this)));
    }

    // if there is remaining rewards to whip for example, we can exit the pool and claim back reward if there are no more users in whipper
    function withdrawDust() public onlyOwner nonReentrant {
        require(wCream.totalSupply() == 0,
            "can only withdraw dust if everyone is out of the pool"
        );
        creamPool.exit();
        _crToCream(crCream.balanceOf(address(this)));
        cream.approve(address(owner), cream.balanceOf(address(this)));
        cream.transfer(owner, cream.balanceOf(address(this)));
    }

    // **** Withdraw / Deposit functions ****

    function withdrawAll() external {
        withdraw(wCream.balanceOf(msg.sender));
    }

    function withdraw(uint256 _shares) public canWithdraw nonReentrant {
        uint256 crPTBalance = creamPool.balanceOf(address(this));

        uint256 amount = _shares.mul(crPTBalance).div(wCream.totalSupply());
        wCream.burn(msg.sender, _shares);

        // Withdraw from pool contract
        creamPool.withdraw(amount);

        // Retrive shares from Uniswap pool and converts to SUSHI
        uint256 _before = cream.balanceOf(address(this));
        _crToCream(amount);
        uint256 _after = cream.balanceOf(address(this));

        // Transfer back SUSHI difference
        cream.transfer(msg.sender, _after.sub(_before));
    }

    function depositAll() external {
        deposit(cream.balanceOf(msg.sender));
    }

    function deposit(uint256 _amount) public canReinvest nonReentrant {
        cream.transferFrom(msg.sender, address(this), _amount);

        uint256 _pool = creamPool.balanceOf(address(this));
        uint256 _before = crCream.balanceOf(address(this));
        _creamToCr(_amount);
        uint256 _after = crCream.balanceOf(address(this));

        _amount = _after.sub(_before); // Additional check for deflationary tokens

        uint256 shares = 0;
        if (wCream.totalSupply() == 0) {
            shares = _amount;
        } else {
            shares = _amount.mul(wCream.totalSupply()).div(_pool);
        }

        // Deposit into Masterchef contract to get rewards
        crCream.approve(address(creamPool), _amount);
        creamPool.stake(_amount);

        wCream.mint(msg.sender, shares);
    }

    function _crToCream(uint256 _amount) internal {
        crCream.redeem(_amount);
    }

    function _creamToCr(uint256 _amount) internal {
        // Add to cream pool
        cream.approve(address(crCream),_amount);
        crCream.mint(_amount);
    }

    modifier onlyOwner() {
        require(
            msg.sender == owner,
            "Sender not authorized."
        );
        _;
    }

    modifier canReinvest() {
        require(breaker, "deposits and harvests not permitted right now to prevent stake lock");
        _;
    }

    modifier canWithdraw() {
        require(
            creamPool.breaker() || creamPool.stakeLock(address(this)) < block.number,
            "stake locked by cream"
        );
        _;
    }

    modifier requireRewardsEnded() {
        require(
            block.timestamp + 12 hours >= creamPool.periodFinish(),
            "pool is not closed"
        );
        _;
    }

}
