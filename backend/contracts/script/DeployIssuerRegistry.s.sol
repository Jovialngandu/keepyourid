// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import {IssuerRegistry} from "../src/IssuerRegistry.sol";

contract DeployIssuerRegistry is Script {
    function run() external {
        vm.startBroadcast();
        IssuerRegistry registry = new IssuerRegistry();
        vm.stopBroadcast();

        console.log("ISSUER_REGISTRY_ADDRESS=%s", address(registry));
    }
}
