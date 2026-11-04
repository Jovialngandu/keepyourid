import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  createDID,
  createDIDChallenge,
  getOrganizationDids,
  verifyDID,
  registerIssuer,
} from "../services/did";


import { connectWallet, signMessage } from "../utils/wallet";

import "../styles/did-setup.css";

function buildDIDDocument(identifier, address) {
  const methodId = `${identifier}#controller`;

  return {
    id: identifier,
    verificationMethod: [
      {
        id: methodId,
        type: "EcdsaSecp256k1RecoveryMethod2020",
        controller: identifier,
        blockchainAccountId: `eip155:11155111:${address}`,
      },
    ],
    authentication: [methodId],
  };
}

export default function DIDSetup() {
  const { organizationId } = useParams();

  const [account, setAccount] = useState("");
  const [did, setDid] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [verification, setVerification] = useState(null);


const [issuer, setIssuer] = useState(null);
const [registeringIssuer, setRegisteringIssuer] = useState(false);



  
  useEffect(() => {
    async function loadDID() {
      try {
        const result = await getOrganizationDids(organizationId);
        const items = Array.isArray(result)
          ? result
          : result?.items || [];

        setDid(items[0] || null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadDID();
  }, [organizationId]);

  async function handleConnectWallet() {
    setError("");
    setSuccess("");

    try {
      const address = await connectWallet();
      setAccount(address);
    } catch (err) {
      setError(err.message);
    }
  }


async function handleRegisterIssuer() {
  if (!did || did.status !== "VERIFIED") {
    setError("Le DID doit d'abord être vérifié.");
    return;
  }

  if (!account) {
    setError("Connecte ton wallet avant de continuer.");
    return;
  }

  setRegisteringIssuer(true);
  setError("");
  setSuccess("");
  setIssuer(null);

  try {
    const result = await registerIssuer(organizationId, {
      did_id: did.id,
    });

    setIssuer(result);
    setSuccess("Enregistrement de l'émetteur effectué.");
  } catch (err) {
    setError(err.message);
  } finally {
    setRegisteringIssuer(false);
  }
}



async function handleAssociateDID() {
  if (!account) {
    setError("Connecte d'abord ton wallet.");
    return;
  }

  setProcessing(true);
  setError("");
  setSuccess("");

  try {
    const identifier = `did:ethr:sepolia:${account}`;

    const result = await createDID(organizationId, {
      identifier,
      method: "ethr",
      document: buildDIDDocument(identifier, account),
    });

    setDid(result);
    setSuccess("DID associé à ton organisation.");
  } catch (err) {
    const alreadyRegistered =
      err.status === 409 ||
      err.message?.toLowerCase().includes("already registered");

    if (alreadyRegistered) {
      setError(
        "Ce DID existe déjà. Il ne peut pas être créé une seconde fois. " +
        "Vérifie s'il est déjà associé à une autre organisation."
      );
    } else {
      setError(err.message || "Impossible d'associer le DID.");
    }
  } finally {
    setProcessing(false);
  }
}


  async function handleVerifyDID() {
    if (!did || !account) {
      setError("DID ou wallet manquant.");
      return;
    }

    setProcessing(true);
    setError("");
    setSuccess("");
    setVerification(null);

    try {
      const challenge = await createDIDChallenge(did.id, {
        purpose: "did_authentication",
        domain: window.location.host,
      });

      const signature = await signMessage(
        challenge.message,
        account
      );

      const result = await verifyDID(did.id, {
        challenge_id: challenge.challenge_id,
        verification_method: `${did.identifier}#controller`,
        signature,
      });

      setVerification(result);
      setDid((previous) => ({
        ...previous,
        status: result.status,
      }));

      setSuccess("La vérification du DID a été effectuée.");
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  }

  if (loading) {
    return <main className="did-page">Chargement de l'identité...</main>;
  }

  return (
    <main className="did-page">
      <header className="did-header">
        <Link to={`/organizations/${organizationId}`}>
          ← Retour au dashboard
        </Link>

        <span className="did-eyebrow">IDENTITÉ NUMÉRIQUE</span>
        <h1>Connect your identity.</h1>
        <p>
          Associe une identité décentralisée à ton organisation et
          prouve que tu contrôles la clé correspondante.
        </p>
      </header>

      {error && <div className="did-alert error">{error}</div>}
      {success && <div className="did-alert success">{success}</div>}

      <section className="did-card">
        <div className="did-step">01 — WALLET</div>
        <h2>Connect your wallet</h2>
        <p>
          Ton wallet permet de prouver le contrôle de l'adresse
          utilisée par ton identité numérique.
        </p>

        {account ? (
          <div className="did-wallet-address">
            <span>Wallet connecté</span>
            <code>{account}</code>
          </div>
        ) : (
          <button
            className="did-primary-button"
            onClick={handleConnectWallet}
            disabled={processing}
          >
            Connect wallet
          </button>
        )}
      </section>

      <section className="did-card">
        <div className="did-step">02 — DECENTRALIZED IDENTITY</div>
        <h2>Associate your DID</h2>

        {did ? (
          <div className="did-information">
            <span>DID associé</span>
            <code>{did.identifier}</code>

            <div className="did-status">
              Statut : <strong>{did.status || "CREATED"}</strong>
            </div>
          </div>
        ) : (
          <>
            <p>
              Nous allons créer une identité basée sur ton adresse
              publique Ethereum.
            </p>

            <button
              className="did-primary-button"
              onClick={handleAssociateDID}
              disabled={!account || processing}
            >
              {processing ? "Association..." : "Associate DID"}
            </button>
          </>
        )}
      </section>

      <section className="did-card">
        <div className="did-step">03 — OWNERSHIP PROOF</div>
        <h2>Verify ownership</h2>
        <p>
          KeepYourID génère un challenge unique. Ton wallet signe
          le message et le backend vérifie la signature.
        </p>

        <button
          className="did-primary-button"
          onClick={handleVerifyDID}
          disabled={!account || !did || processing || did.status === "VERIFIED"}
        >
          {processing
            ? "Verification..."
            : did?.status === "VERIFIED"
              ? "DID verified"
              : "Verify DID"}
        </button>

        {verification && (
          <div className="did-verification-result">
            <strong>Verification result</strong>
            <p>Status : {verification.status}</p>
            <p>Signer : {verification.signer_address}</p>
            <p>
              Verification method :{" "}
              {verification.verification_method}
            </p>
          </div>
        )}
      </section>


<section className="did-card">
  <div className="did-step">04 — BLOCKCHAIN REGISTRATION</div>

  <h2>Register your issuer identity</h2>

  <p>
    Enregistre ton organisation comme émetteur sur le registre
    blockchain KeepYourID.
  </p>

  <button
    className="did-primary-button"
    onClick={handleRegisterIssuer}
    disabled={
      !did ||
      did.status !== "VERIFIED" ||
      registeringIssuer ||
      Boolean(issuer)
    }
  >
    {registeringIssuer
      ? "Registering on blockchain..."
      : issuer
        ? "Issuer registered"
        : "Register issuer"}
  </button>

  {issuer && (
    <div className="did-verification-result">
      <strong>Issuer registration result</strong>

      <p>
        Status: {issuer.status || issuer.is_registered ? "Registered" : "Submitted"}
      </p>

      {issuer.transaction_hash && (
        <p>
          Transaction:
          <code>{issuer.transaction_hash}</code>
        </p>
      )}

      {issuer.tx_hash && (
        <p>
          Transaction:
          <code>{issuer.tx_hash}</code>
        </p>
      )}
    </div>
  )}
</section>

    </main>
  );
}