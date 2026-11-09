
import { useCallback, useEffect, useState } from "react";

import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import CredentialQrModal from "../components/verification/CredentialQrModal";

import {
  connectWallet,
  signMessage,
} from "../utils/wallet";

import {
  getHolderDIDs,
  registerHolderDID,
  createHolderDIDChallenge,
  verifyHolderDID,
  getHolderCredentials,
} from "../services/holder";

import "../styles/Wallet.css";

const SEPOLIA_CHAIN_ID = "0xaa36a7";
const DID_PURPOSE = "did_authentication";

function shortenAddress(value) {
  if (!value) return "";
  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

function extractItems(result) {
  if (Array.isArray(result)) return result;
  if (Array.isArray(result?.items)) return result.items;
  if (Array.isArray(result?.results)) return result.results;
  if (Array.isArray(result?.data)) return result.data;
  return [];
}

function buildHolderDIDDocument(did, account) {
  const verificationMethod = `${did}#controller`;

  return {
    id: did,
    verificationMethod: [
      {
        id: verificationMethod,
        type: "EcdsaSecp256k1RecoveryMethod2020",
        controller: did,
        blockchainAccountId: `eip155:11155111:${account}`,
      },
    ],
    authentication: [verificationMethod],
  };
}

export default function Wallet() {
  const [account, setAccount] = useState("");
  const [chainId, setChainId] = useState("");

  const [holderDID, setHolderDID] = useState(null);
  const [credentials, setCredentials] = useState([]);

  const [connecting, setConnecting] = useState(false);
  const [loadingCredentials, setLoadingCredentials] = useState(false);

  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [qrCredential, setQrCredential] = useState(null);

  const [verified, setVerified] = useState(false);

  const did = account
    ? `did:ethr:sepolia:${account}`
    : "";

  const connected = Boolean(account);
  const correctNetwork = chainId === SEPOLIA_CHAIN_ID;

  // Récupérer les credentials du titulaire.
  const loadCredentials = useCallback(async () => {
    setLoadingCredentials(true);

    try {
      const result = await getHolderCredentials();
      setCredentials(extractItems(result));
    } catch (err) {
      setError(
        err.message || "Impossible de charger vos credentials."
      );
    } finally {
      setLoadingCredentials(false);
    }
  }, []);

  // Récupérer ou créer le DID associé à l'utilisateur connecté.
  async function getOrCreateHolderDID(identifier, document) {
    const result = await getHolderDIDs();
    const existingDIDs = extractItems(result);

    const existingDID = existingDIDs.find(
      (item) => item.identifier === identifier
    );

    if (existingDID) {
      return existingDID;
    }

    return registerHolderDID({
      identifier,
      method: "ethr",
      document,
    });
  }

  // Associer le DID, signer le challenge et vérifier la preuve.
  async function authenticateHolder(address) {


	
    const identifier = `did:ethr:sepolia:${address}`;
    const document = buildHolderDIDDocument(
      identifier,
      address
    );

    // 1. Association du DID au compte utilisateur.
    const registeredDID = await getOrCreateHolderDID(
      identifier,
      document
    );

    if (!registeredDID?.id) {
      throw new Error(
        "Le backend n'a pas retourné l'identifiant du DID."
      );
    }


		

    setHolderDID(registeredDID);

    // 2. Création du challenge.
    const purpose = DID_PURPOSE;
    const domain = window.location.host;



	
    const challenge = await createHolderDIDChallenge(
      registeredDID.id,
      {
        purpose,
        domain,
      }
    );

    if (!challenge?.message || !challenge?.challenge_id) {
      throw new Error(
        "Le backend a retourné un challenge incomplet."
      );
    }

    // 3. Signature du message exact retourné par le backend.
    const verificationMethod = `${identifier}#controller`;



console.log("ACCOUNT USED:", address);
console.log("DID:", identifier);
console.log("MESSAGE:", challenge.message);

const activeAccounts = await window.ethereum.request({
  method: "eth_accounts",
});
console.log("METAMASK ACTIVE ACCOUNT:", activeAccounts[0]);

if (activeAccounts[0]?.toLowerCase() !== address.toLowerCase()) {
  throw new Error("Le compte MetaMask actif ne correspond pas au compte utilisé pour le DID.");
}

    const signature = await signMessage(
      challenge.message,
      address
    );
    console.log("SIGNATURE:", signature);

    // 4. Vérification cryptographique côté backend.
    const verification = await verifyHolderDID(
      registeredDID.id,
      {
        challenge_id: challenge.challenge_id,
        signature,
        verification_method: verificationMethod,
        purpose,
        domain,
      }
    );

    // Une réponse HTTP réussie signifie que le backend
    // a accepté la preuve.
    setVerified(true);

    setHolderDID((previous) => ({
      ...previous,
      ...registeredDID,
      status: verification?.status || "VERIFIED",
    }));

    // 5. Chargement des credentials du titulaire.
    await loadCredentials();
  }

  async function handleConnect() {
    setConnecting(true);
    setError("");

    try {
      let address = account;

      if (!address) {
        address = await connectWallet();
      } else if (!correctNetwork) {
        address = await connectWallet();
      }

      const network = await window.ethereum.request({
        method: "eth_chainId",
      });

      setAccount(address);
      setChainId(network);

      if (network !== SEPOLIA_CHAIN_ID) {
        throw new Error(
          "Connecte ton wallet au réseau Sepolia."
        );
      }

      await authenticateHolder(address);

    } catch (err) {
      setVerified(false);
      setError(
        err.message || "Une erreur est survenue pendant la connexion."
      );
    } finally {
      setConnecting(false);
    }
  }

  async function handleCopy() {
    if (!did) return;

    try {
      await navigator.clipboard.writeText(did);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Impossible de copier le DID.");
    }
  }

  // Écouter les changements de compte et de réseau MetaMask.
  useEffect(() => {
    if (!window.ethereum) return;

    async function initializeWallet() {
      try {
        const accounts = await window.ethereum.request({
          method: "eth_accounts",
        });

        const network = await window.ethereum.request({
          method: "eth_chainId",
        });

        setAccount(accounts?.[0] || "");
        setChainId(network);
      } catch {
        // Le wallet pourra être connecté manuellement.
      }
    }

    function handleAccountsChanged(accounts) {
      setAccount(accounts?.[0] || "");
      setHolderDID(null);
      setCredentials([]);
      setVerified(false);
      setError("");
    }

    function handleChainChanged(network) {
      setChainId(network);
      setHolderDID(null);
      setCredentials([]);
      setVerified(false);

      if (network !== SEPOLIA_CHAIN_ID) {
        setError(
          "Veuillez reconnecter votre wallet au réseau Sepolia."
        );
      } else {
        setError("");
      }
    }

    initializeWallet();

    window.ethereum.on(
      "accountsChanged",
      handleAccountsChanged
    );

    window.ethereum.on(
      "chainChanged",
      handleChainChanged
    );

    return () => {
      window.ethereum.removeListener(
        "accountsChanged",
        handleAccountsChanged
      );

      window.ethereum.removeListener(
        "chainChanged",
        handleChainChanged
      );
    };
  }, []);

  return (
    <>
      <Navbar />

      <main className="wallet-page">
        <header className="wallet-header">
          <div>
            <span className="wallet-eyebrow">
              IDENTITÉ NUMÉRIQUE PERSONNELLE
            </span>

            <h1>Mon Wallet</h1>

            <p>
              Votre identité numérique, vos credentials et vos preuves
              vérifiables réunis dans un espace personnel.
            </p>
          </div>

          <div className="wallet-header-symbol">KYID</div>
        </header>

        {error && (
          <div className="wallet-alert" role="alert">
            {error}
          </div>
        )}

        {!connected ? (
          <section className="wallet-connect-card">
            <div className="wallet-connect-icon">◇</div>

            <span className="wallet-eyebrow">
              VOTRE IDENTITÉ VOUS APPARTIENT
            </span>

            <h2>Commencez avec votre wallet</h2>

            <p>
              Connectez MetaMask pour associer votre identité
              décentralisée à votre compte KeepYourID.
            </p>

            <button
              className="wallet-primary-button"
              onClick={handleConnect}
              disabled={connecting}
            >
              {connecting
                ? "Connexion en cours..."
                : "Connecter MetaMask"}

              {!connecting && <span>→</span>}
            </button>

            <small>
              Réseau requis : Ethereum Sepolia. Votre clé privée
              reste dans votre wallet.
            </small>
          </section>
        ) : (
          <>
            <section className="wallet-overview">
              <div className="wallet-overview-heading">
                <div>
                  <span className="wallet-eyebrow">
                    MON IDENTITÉ
                  </span>

                  <h2>Identité décentralisée</h2>
                </div>

                <span
                  className={`wallet-status ${
                    correctNetwork
                      ? "wallet-status-connected"
                      : ""
                  }`}
                >
                  {correctNetwork
                    ? "Wallet connecté"
                    : "Réseau incorrect"}
                </span>
              </div>

              <div className="wallet-identity-panel">
                <div className="wallet-identity-icon">ID</div>

                <div className="wallet-identity-content">
                  <span>DID TITULAIRE</span>

                  <strong>{shortenAddress(account)}</strong>

                  <small>{did}</small>
                </div>

                <button
                  className="wallet-copy-button"
                  onClick={handleCopy}
                >
                  {copied ? "Copié" : "Copier le DID"}
                </button>
              </div>

              <div className="wallet-information-grid">
                <div className="wallet-information-item">
                  <span>Adresse Ethereum</span>
                  <strong>{shortenAddress(account)}</strong>
                </div>

                <div className="wallet-information-item">
                  <span>Réseau</span>
                  <strong>
                    {correctNetwork ? "Sepolia" : "Non compatible"}
                  </strong>
                </div>

                <div className="wallet-information-item">
                  <span>Statut DID</span>

                  <strong
                    className={
                      verified
                        ? "wallet-status-connected"
                        : "wallet-unverified"
                    }
                  >
                    {verified
                      ? "Vérifié par le backend"
                      : holderDID
                        ? holderDID.status || "Associé, non vérifié"
                        : "Non associé"}
                  </strong>
                </div>
              </div>

              {!verified && (
                <button
                  className="wallet-primary-button"
                  onClick={handleConnect}
                  disabled={connecting || !correctNetwork}
                >
                  {connecting
                    ? "Vérification en cours..."
                    : holderDID
                      ? "Vérifier mon DID"
                      : "Associer et vérifier mon DID"}
                </button>
              )}
            </section>

            <section className="wallet-section">
              <div className="wallet-section-heading">
                <div>
                  <span className="wallet-eyebrow">
                    MES DOCUMENTS
                  </span>

                  <h2>Mes credentials</h2>
                </div>

                <span className="wallet-count">
                  {loadingCredentials
                    ? "Chargement..."
                    : `${credentials.length} document(s)`}
                </span>
              </div>

              {credentials.length > 0 ? (
                <div className="wallet-credentials-list">
                  {credentials.map((credential) => (
                    <div
                      className="wallet-credential-item"
                      key={credential.id}
                    >
                      <div>
                        <strong>
                          {credential.type?.join(", ") ||
                            credential.credential_type ||
                            "Credential vérifiable"}
                        </strong>

                        <small>
                          {credential.id}
                        </small>
                      </div>

                      <div className="wallet-credential-actions">
                        <span>
                          {credential.status || "Émise"}
                        </span>

                        {credential.signed_credential ? (
                          <button
                            type="button"
                            className="wallet-qr-button"
                            onClick={() => setQrCredential(credential)}
                          >
                            Afficher mon QR code
                          </button>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="wallet-empty-state">
                  <div className="wallet-empty-icon">▤</div>

                  <h3>
                    {loadingCredentials
                      ? "Chargement de vos credentials..."
                      : "Aucune credential pour le moment"}
                  </h3>

                  <p>
                    Les attestations et documents numériques qui
                    vous seront délivrés apparaîtront ici.
                  </p>

                  <span>
                    Réception des credentials
                  </span>
                </div>
              )}
            </section>

            <section className="wallet-security-note">
              <div>◇</div>

              <p>
                <strong>
                  Votre identité reste sous votre contrôle.
                </strong>
                <br />

                Votre DID est associé à votre compte KeepYourID.
                La preuve de contrôle est signée dans MetaMask
                et vérifiée cryptographiquement par le backend.
                Vos credentials sont chargés depuis votre espace
                titulaire.
              </p>
            </section>

            {qrCredential && (
              <CredentialQrModal
                credential={qrCredential}
                onClose={() => setQrCredential(null)}
              />
            )}
          </>
        )}
      </main>

      <Footer />
    </>
  );
}
