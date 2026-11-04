const SEPOLIA_CHAIN_ID = "0xaa36a7";

export async function connectWallet() {
  if (!window.ethereum) {
    throw new Error(
      "Aucun wallet compatible détecté. Installe ou active MetaMask."
    );
  }

  const accounts = await window.ethereum.request({
    method: "eth_requestAccounts",
  });

  if (!accounts.length) {
    throw new Error("Aucun compte wallet disponible.");
  }

  let chainId = await window.ethereum.request({
    method: "eth_chainId",
  });

  if (chainId !== SEPOLIA_CHAIN_ID) {
    try {
      await window.ethereum.request({
        method: "wallet_switchEthereumChain",
        params: [{ chainId: SEPOLIA_CHAIN_ID }],
      });
    } catch (error) {
      if (error.code === 4902) {
        throw new Error(
          "Le réseau Sepolia n'est pas configuré dans ton wallet."
        );
      }

      throw error;
    }
  }

  chainId = await window.ethereum.request({
    method: "eth_chainId",
  });

  if (chainId !== SEPOLIA_CHAIN_ID) {
    throw new Error("Connecte ton wallet au réseau Sepolia.");
  }

  return accounts[0];
}

export async function signMessage(message, account) {
  const messageBytes = new TextEncoder().encode(message);

  const messageHex =
    "0x" +
    Array.from(messageBytes)
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");

  return window.ethereum.request({
    method: "personal_sign",
    params: [messageHex, account],
  });
}