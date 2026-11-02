// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {IssuerRegistry} from "../src/IssuerRegistry.sol";

contract IssuerRegistryTest is Test {
    IssuerRegistry private registry;

    address private owner;
    address private registrar = address(0x2);
    address private unauthorized = address(0x3);
    address private newOwner = address(0x4);

    bytes32 private didHash = keccak256("did:ethr:sepolia:issuer-1");
    bytes32 private metadataHash = keccak256("issuer-metadata-v1");

    function setUp() public {
        owner = address(this);
        registry = new IssuerRegistry();
    }

    // ---------------------------------------------------------
    // Deployment and access control
    // ---------------------------------------------------------

    function test_ConstructorSetsOwnerAsRegistrar() public view {
        assertEq(registry.owner(), owner);
        assertTrue(registry.registrars(owner));
    }

    function test_OwnerCanAuthorizeRegistrar() public {
        vm.prank(owner);
        registry.setRegistrar(registrar, true);

        assertTrue(registry.registrars(registrar));
    }

    function test_OwnerCanRevokeRegistrar() public {
        vm.startPrank(owner);
        registry.setRegistrar(registrar, true);
        registry.setRegistrar(registrar, false);
        vm.stopPrank();

        assertFalse(registry.registrars(registrar));
    }

    function test_OwnerCannotRevokeOwnRegistrarRole() public {
        vm.prank(owner);

        vm.expectRevert(bytes("Owner must remain registrar"));

        registry.setRegistrar(owner, false);
    }

    function test_UnauthorizedAddressCannotAuthorizeRegistrar() public {
        vm.prank(unauthorized);

        vm.expectRevert(bytes("Not contract owner"));

        registry.setRegistrar(registrar, true);
    }

    function test_RegistrarCannotManageOtherRegistrars() public {
        vm.prank(owner);
        registry.setRegistrar(registrar, true);

        vm.prank(registrar);

        vm.expectRevert(bytes("Not contract owner"));

        registry.setRegistrar(unauthorized, true);
    }

    function test_CannotAuthorizeZeroAddress() public {
        vm.prank(owner);

        vm.expectRevert(bytes("Invalid address"));

        registry.setRegistrar(address(0), true);
    }

    // ---------------------------------------------------------
    // Issuer registration
    // ---------------------------------------------------------

    function test_RegistrarCanRegisterIssuer() public {
        vm.prank(owner);
        registry.registerIssuer(didHash, metadataHash);

        IssuerRegistry.Issuer memory issuer = registry.getIssuer(didHash);

        assertEq(issuer.didHash, didHash);
        assertEq(issuer.metadataHash, metadataHash);
        assertEq(
            uint256(issuer.status), uint256(IssuerRegistry.IssuerStatus.ACTIVE)
        );

        assertTrue(registry.isRegistered(didHash));
        assertTrue(registry.isActive(didHash));
        assertGt(issuer.registeredAt, 0);
        assertEq(issuer.registeredAt, issuer.updatedAt);
    }

    function test_RegistrationEmitsEvent() public {
        vm.expectEmit(true, false, false, true);

        emit IssuerRegistry.IssuerRegistered(
            didHash, metadataHash, block.timestamp
        );

        registry.registerIssuer(didHash, metadataHash);
    }

    function test_RejectsDuplicateIssuer() public {
        registry.registerIssuer(didHash, metadataHash);

        vm.expectRevert(bytes("Issuer already registered"));

        registry.registerIssuer(didHash, metadataHash);
    }

    function test_RejectsZeroDidHash() public {
        vm.expectRevert(bytes("Invalid DID hash"));

        registry.registerIssuer(bytes32(0), metadataHash);
    }

    function test_RejectsZeroMetadataHash() public {
        vm.expectRevert(bytes("Invalid metadata hash"));

        registry.registerIssuer(didHash, bytes32(0));
    }

    function test_UnauthorizedCannotRegisterIssuer() public {
        vm.prank(unauthorized);

        vm.expectRevert(bytes("Not authorized registrar"));

        registry.registerIssuer(didHash, metadataHash);
    }

    function test_AuthorizedRegistrarCanRegisterIssuer() public {
        vm.prank(owner);
        registry.setRegistrar(registrar, true);

        vm.prank(registrar);
        registry.registerIssuer(didHash, metadataHash);

        assertTrue(registry.isRegistered(didHash));
    }

    // ---------------------------------------------------------
    // Issuer status
    // ---------------------------------------------------------

    function test_RegistrarCanSuspendIssuer() public {
        registry.registerIssuer(didHash, metadataHash);

        registry.updateIssuerStatus(
            didHash, IssuerRegistry.IssuerStatus.SUSPENDED
        );

        assertTrue(registry.isRegistered(didHash));
        assertFalse(registry.isActive(didHash));

        IssuerRegistry.Issuer memory issuer = registry.getIssuer(didHash);

        assertEq(
            uint256(issuer.status),
            uint256(IssuerRegistry.IssuerStatus.SUSPENDED)
        );
    }

    function test_RegistrarCanReactivateIssuer() public {
        registry.registerIssuer(didHash, metadataHash);

        registry.updateIssuerStatus(
            didHash, IssuerRegistry.IssuerStatus.SUSPENDED
        );

        registry.updateIssuerStatus(didHash, IssuerRegistry.IssuerStatus.ACTIVE);

        assertTrue(registry.isActive(didHash));
    }

    function test_StatusChangeEmitsEvent() public {
        registry.registerIssuer(didHash, metadataHash);

        vm.expectEmit(true, false, false, true);

        emit IssuerRegistry.IssuerStatusChanged(
            didHash, IssuerRegistry.IssuerStatus.SUSPENDED, block.timestamp
        );

        registry.updateIssuerStatus(
            didHash, IssuerRegistry.IssuerStatus.SUSPENDED
        );
    }

    function test_CannotSetStatusToNone() public {
        registry.registerIssuer(didHash, metadataHash);

        vm.expectRevert(bytes("Invalid status"));

        registry.updateIssuerStatus(didHash, IssuerRegistry.IssuerStatus.NONE);
    }

    function test_CannotUpdateUnchangedStatus() public {
        registry.registerIssuer(didHash, metadataHash);

        vm.expectRevert(bytes("Status unchanged"));

        registry.updateIssuerStatus(didHash, IssuerRegistry.IssuerStatus.ACTIVE);
    }

    function test_CannotUpdateStatusOfUnknownIssuer() public {
        vm.expectRevert(bytes("Issuer does not exist"));

        registry.updateIssuerStatus(
            didHash, IssuerRegistry.IssuerStatus.SUSPENDED
        );
    }

    // ---------------------------------------------------------
    // Metadata
    // ---------------------------------------------------------

    function test_RegistrarCanUpdateMetadata() public {
        registry.registerIssuer(didHash, metadataHash);

        bytes32 newMetadataHash = keccak256("issuer-metadata-v2");

        registry.updateMetadataHash(didHash, newMetadataHash);

        IssuerRegistry.Issuer memory issuer = registry.getIssuer(didHash);

        assertEq(issuer.metadataHash, newMetadataHash);
    }

    function test_MetadataUpdateEmitsEvent() public {
        registry.registerIssuer(didHash, metadataHash);

        bytes32 newMetadataHash = keccak256("issuer-metadata-v2");

        vm.expectEmit(true, false, false, true);

        emit IssuerRegistry.IssuerMetadataUpdated(
            didHash, newMetadataHash, block.timestamp
        );

        registry.updateMetadataHash(didHash, newMetadataHash);
    }

    function test_CannotSetZeroMetadataHash() public {
        registry.registerIssuer(didHash, metadataHash);

        vm.expectRevert(bytes("Invalid metadata hash"));

        registry.updateMetadataHash(didHash, bytes32(0));
    }

    function test_CannotUpdateUnchangedMetadata() public {
        registry.registerIssuer(didHash, metadataHash);

        vm.expectRevert(bytes("Metadata unchanged"));

        registry.updateMetadataHash(didHash, metadataHash);
    }

    function test_CannotUpdateMetadataOfUnknownIssuer() public {
        vm.expectRevert(bytes("Issuer does not exist"));

        registry.updateMetadataHash(didHash, keccak256("new-metadata"));
    }

    // ---------------------------------------------------------
    // Ownership
    // ---------------------------------------------------------

    function test_OwnerCanTransferOwnership() public {
        vm.prank(owner);
        registry.transferOwnership(newOwner);

        assertEq(registry.owner(), newOwner);
        assertTrue(registry.registrars(newOwner));
        assertFalse(registry.registrars(owner));
    }

    function test_PreviousOwnerCannotManageRegistryAfterTransfer() public {
        vm.prank(owner);
        registry.transferOwnership(newOwner);

        vm.prank(owner);

        vm.expectRevert(bytes("Not contract owner"));

        registry.setRegistrar(unauthorized, true);
    }

    function test_NewOwnerCanManageRegistryAfterTransfer() public {
        vm.prank(owner);
        registry.transferOwnership(newOwner);

        vm.prank(newOwner);
        registry.setRegistrar(registrar, true);

        assertTrue(registry.registrars(registrar));
    }

    function test_CannotTransferOwnershipToZeroAddress() public {
        vm.prank(owner);

        vm.expectRevert(bytes("Invalid owner"));

        registry.transferOwnership(address(0));
    }
}
