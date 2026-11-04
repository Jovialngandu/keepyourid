import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import { connectWallet } from "../utils/wallet";
import "../styles/Wallet.css";

const SEPOLIA_CHAIN_ID = "0xaa36a7";

function shortenAddress(value) {
  if (!value) return "";
  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

export default function Wallet() {
  const [account, setAccount] = useState("");
  const [chainId, setChainId] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const did = account ? `did:ethr:sepolia:${account}` : "";
  const connected = Boolean(account);
  const correctNetwork = chainId === SEPOLIA_CHAIN_ID;

  async function handleConnect() {
    setConnecting(true);
    setError("");

    try {
      const address = await connectWallet();
      const network = await window.ethereum.request({
        method: "eth_chainId",
      });

      setAccount(address);
      setChainId(network);
    } catch (err) {
      setError(err.message || "Impossible de connecter le wallet.");
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

  useEffect(() => {
    if (!window.ethereum) return;

    function handleAccountsChanged(accounts) {
      setAccount(accounts?.[0] || "");
      setError("");
    }

    function handleChainChanged(network) {
      setChainId(network);

      if (network !== SEPOLIA_CHAIN_ID) {
        setError("Veuillez reconnecter votre wallet au réseau Sepolia.");
      } else {
        setError("");
      }
    }

    window.ethereum.on("accountsChanged", handleAccountsChanged);
    window.ethereum.on("chainChanged", handleChainChanged);

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
              Connectez MetaMask pour créer votre identité décentralisée
              à partir de votre adresse Ethereum.
            </p>

            <button
              className="wallet-primary-button"
              onClick={handleConnect}
              disabled={connecting}
            >
              {connecting ? "Connexion en cours..." : "Connecter MetaMask"}
              {!connecting && <span>→</span>}
            </button>

            <small>
              Réseau requis : Ethereum Sepolia. Votre clé privée reste
              dans votre wallet.
            </small>
          </section>
        ) : (
          <>
            <section className="wallet-overview">
              <div className="wallet-overview-heading">
                <div>
                  <span className="wallet-eyebrow">MON IDENTITÉ</span>
                  <h2>Identité décentralisée</h2>
                </div>

                <span
                  className={`wallet-status ${
                    correctNetwork ? "wallet-status-connected" : ""
                  }`}
                >
                  {correctNetwork ? "Wallet connecté" : "Réseau incorrect"}
                </span>
              </div>

              <div className="wallet-identity-panel">
                <div className="wallet-identity-icon">ID</div>

                <div className="wallet-identity-content">
                  <span>HOLDER DID</span>
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
                  <strong className="wallet-unverified">
                    Non vérifié par le backend
                  </strong>
                </div>
              </div>

              {!correctNetwork && (
                <button
                  className="wallet-primary-button"
                  onClick={handleConnect}
                  disabled={connecting}
                >
                  Reconnecter sur Sepolia
                </button>
              )}
            </section>

            <section className="wallet-section">
              <div className="wallet-section-heading">
                <div>
                  <span className="wallet-eyebrow">MES DOCUMENTS</span>
                  <h2>Mes credentials</h2>
                </div>
                <span className="wallet-count">0 document</span>
              </div>

              <div className="wallet-empty-state">
                <div className="wallet-empty-icon">▤</div>
                <h3>Aucune credential pour le moment</h3>
                <p>
                  Les attestations et documents numériques qui vous seront
                  délivrés apparaîtront ici.
                </p>
                <span>Réception des credentials à venir</span>
              </div>
            </section>

            <section className="wallet-security-note">
              <div>◇</div>
              <p>
                <strong>Votre identité reste sous votre contrôle.</strong>
                <br />
                Cette première version affiche votre DID dérivé de MetaMask.
                La vérification cryptographique par le backend et le stockage
                des credentials seront intégrés dans les prochaines étapes.
              </p>
            </section>
          </>
        )}
      </main>

      <Footer />
    </>
  );
}