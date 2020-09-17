pragma solidity ^0.5.16;

interface StakingRewardsLock {
    function DURATION (  ) external view returns ( uint256 );
    function admin (  ) external view returns ( address );
    function balanceOf ( address account ) external view returns ( uint256 );
    function breaker (  ) external view returns ( bool );
    function cream (  ) external view returns ( address );
    function earned ( address account ) external view returns ( uint256 );
    function exit (  ) external;
    function getReward (  ) external;
    function isOwner (  ) external view returns ( bool );
    function lastTimeRewardApplicable (  ) external view returns ( uint256 );
    function lastUpdateTime (  ) external view returns ( uint256 );
    function lock (  ) external view returns ( uint256 );
    function lpToken (  ) external view returns ( address );
    function notifyRewardAmount ( uint256 reward, uint256 _duration ) external;
    function owner (  ) external view returns ( address );
    function periodFinish (  ) external view returns ( uint256 );
    function renounceOwnership (  ) external;
    function rewardPerToken (  ) external view returns ( uint256 );
    function rewardPerTokenStored (  ) external view returns ( uint256 );
    function rewardRate (  ) external view returns ( uint256 );
    function rewards ( address ) external view returns ( uint256 );
    function seize ( address _token, uint256 amount ) external;
    function setBreaker ( bool _breaker ) external;
    function setRewardDistribution ( address _rewardDistribution ) external;
    function stake ( uint256 amount ) external;
    function stakeLock ( address ) external view returns ( uint256 );
    function totalSupply (  ) external view returns ( uint256 );
    function transferOwnership ( address newOwner ) external;
    function userRewardPerTokenPaid ( address ) external view returns ( uint256 );
    function withdraw ( uint256 amount ) external;
}