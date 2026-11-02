// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IssuerRegistry
/// @notice Public on-chain registry of credential issuers.
/// @dev Registration does not imply legal recognition or trust.
contract IssuerRegistry {
    address public owner;

    enum IssuerStatus {
        NONE,
        ACTIVE,
        SUSPENDED
    }

    struct Issuer {
        bytes32 didHash;
        bytes32 metadataHash;
        IssuerStatus status;
        uint256 registeredAt;
        uint256 updatedAt;
    }

    mapping(bytes32 => Issuer) private issuers;
    mapping(address => bool) public registrars;

    event OwnershipTransferred(
        address indexed previousOwner, address indexed newOwner
    );

    event RegistrarUpdated(address indexed registrar, bool authorized);

    event IssuerRegistered(
        bytes32 indexed didHash, bytes32 metadataHash, uint256 timestamp
    );

    event IssuerStatusChanged(
        bytes32 indexed didHash, IssuerStatus status, uint256 timestamp
    );

    event IssuerMetadataUpdated(
        bytes32 indexed didHash, bytes32 metadataHash, uint256 timestamp
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Not contract owner");
        _;
    }

    modifier onlyRegistrar() {
        require(registrars[msg.sender], "Not authorized registrar");
        _;
    }

    constructor() {
        owner = msg.sender;
        registrars[msg.sender] = true;

        emit RegistrarUpdated(msg.sender, true);
    }

    // ---------------------------------------------------------
    // Access management
    // ---------------------------------------------------------

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        require(newOwner != owner, "Already owner");

        address previousOwner = owner;

        owner = newOwner;
        registrars[newOwner] = true;

        // The former owner loses registrar access.
        registrars[previousOwner] = false;

        emit RegistrarUpdated(previousOwner, false);
        emit RegistrarUpdated(newOwner, true);
        emit OwnershipTransferred(previousOwner, newOwner);
    }

    function setRegistrar(address registrar, bool authorized)
        external
        onlyOwner
    {
        require(registrar != address(0), "Invalid address");
        require(registrar != owner || authorized, "Owner must remain registrar");

        registrars[registrar] = authorized;

        emit RegistrarUpdated(registrar, authorized);
    }

    // ---------------------------------------------------------
    // Issuer registration
    // ---------------------------------------------------------

    function registerIssuer(bytes32 didHash, bytes32 metadataHash)
        external
        onlyRegistrar
    {
        require(didHash != bytes32(0), "Invalid DID hash");
        require(metadataHash != bytes32(0), "Invalid metadata hash");
        require(
            issuers[didHash].status == IssuerStatus.NONE,
            "Issuer already registered"
        );

        uint256 timestamp = block.timestamp;

        issuers[didHash] = Issuer({
            didHash: didHash,
            metadataHash: metadataHash,
            status: IssuerStatus.ACTIVE,
            registeredAt: timestamp,
            updatedAt: timestamp
        });

        emit IssuerRegistered(didHash, metadataHash, timestamp);
    }

    // ---------------------------------------------------------
    // Issuer management
    // ---------------------------------------------------------

    function updateIssuerStatus(bytes32 didHash, IssuerStatus newStatus)
        external
        onlyRegistrar
    {
        Issuer storage issuer = issuers[didHash];

        require(issuer.status != IssuerStatus.NONE, "Issuer does not exist");

        require(newStatus != IssuerStatus.NONE, "Invalid status");

        require(issuer.status != newStatus, "Status unchanged");

        issuer.status = newStatus;
        issuer.updatedAt = block.timestamp;

        emit IssuerStatusChanged(didHash, newStatus, block.timestamp);
    }

    function updateMetadataHash(bytes32 didHash, bytes32 newMetadataHash)
        external
        onlyRegistrar
    {
        Issuer storage issuer = issuers[didHash];

        require(issuer.status != IssuerStatus.NONE, "Issuer does not exist");

        require(newMetadataHash != bytes32(0), "Invalid metadata hash");

        require(issuer.metadataHash != newMetadataHash, "Metadata unchanged");

        issuer.metadataHash = newMetadataHash;
        issuer.updatedAt = block.timestamp;

        emit IssuerMetadataUpdated(didHash, newMetadataHash, block.timestamp);
    }

    // ---------------------------------------------------------
    // Public queries
    // ---------------------------------------------------------

    function getIssuer(bytes32 didHash) external view returns (Issuer memory) {
        require(
            issuers[didHash].status != IssuerStatus.NONE,
            "Issuer does not exist"
        );

        return issuers[didHash];
    }

    function isRegistered(bytes32 didHash) external view returns (bool) {
        return issuers[didHash].status != IssuerStatus.NONE;
    }

    function isActive(bytes32 didHash) external view returns (bool) {
        return issuers[didHash].status == IssuerStatus.ACTIVE;
    }
}
