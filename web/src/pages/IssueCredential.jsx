
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import "../styles/issue-credential.css";

export default function IssueCredential() {
  const { organizationId } = useParams();

  const [credentialType, setCredentialType] = useState("");
  const [holderDID, setHolderDID] = useState("");
  const [claims, setClaims] = useState('{\n  \n}');
  const [error, setError] = useState("");

  function validateCredential() {
    setError("");

    if (!credentialType.trim()) {
      setError("Le type de credential est obligatoire.");
      return false;
    }

    if (!holderDID.trim().startsWith("did:")) {
      setError("Saisis un DID valide pour le détenteur.");
      return false;
    }

    try {
      const parsed = JSON.parse(claims);

      if (
        !parsed ||
        typeof parsed !== "object" ||
        Array.isArray(parsed) ||
        Object.keys(parsed).length === 0
      ) {
        setError("Les données du credential doivent être un objet JSON non vide.");
        return false;
      }
    } catch {
      setError("Les données fournies ne constituent pas un JSON valide.");
      return false;
    }

    return true;
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (!validateCredential()) return;

    setError(
      "Le formulaire est prêt. L'émission réelle sera activée après raccordement au service backend de création et de signature des credentials."
    );
  }

  return (
    <>
      <Navbar />

      <main className="issue-page">
        <header className="issue-header">
          <Link to={`/organizations/${organizationId}`}>
            ← Retour au dashboard
          </Link>

          <span className="issue-eyebrow">VERIFIABLE CREDENTIALS</span>
          <h1>Issue a credential.</h1>
          <p>
            Crée une attestation numérique destinée à un détenteur.
            Elle sera signée par l'identité de ton organisation.
          </p>
        </header>

        <form className="issue-layout" onSubmit={handleSubmit}>
          <section className="issue-card">
            <div className="issue-step">01 — CREDENTIAL INFORMATION</div>
            <h2>Informations du credential</h2>

            <label htmlFor="credentialType">Type de credential</label>
            <input
              id="credentialType"
              value={credentialType}
              onChange={(e) => setCredentialType(e.target.value)}
              placeholder="Ex. CertificateOfParticipation"
              required
            />

            <label htmlFor="holderDID">DID du détenteur</label>
            <input
              id="holderDID"
              value={holderDID}
              onChange={(e) => setHolderDID(e.target.value)}
              placeholder="did:ethr:sepolia:0x..."
              required
            />

            <p className="issue-hint">
              Le DID identifie le détenteur auquel le credential sera attribué.
            </p>
          </section>

          <section className="issue-card">
            <div className="issue-step">02 — CREDENTIAL CLAIMS</div>
            <h2>Données attestées</h2>

            <p>
              Renseigne les informations que ton organisation souhaite
              certifier.
            </p>

            <label htmlFor="claims">Claims (JSON)</label>
            <textarea
              id="claims"
              rows={10}
              value={claims}
              onChange={(e) => setClaims(e.target.value)}
              spellCheck={false}
              required
            />

            <p className="issue-hint">
              Exemple : nom de la formation, organisme, date d'obtention.
              N'ajoute que les informations nécessaires.
            </p>
          </section>

          <section className="issue-card issue-review">
            <div className="issue-step">03 — REVIEW</div>
            <h2>Vérifier avant émission</h2>

            <div className="issue-review-row">
              <span>Type</span>
              <strong>{credentialType || "Non renseigné"}</strong>
            </div>

            <div className="issue-review-row">
              <span>Détenteur</span>
              <strong>{holderDID || "Non renseigné"}</strong>
            </div>

            <div className="issue-review-row">
              <span>Signature</span>
              <strong>À effectuer par le backend</strong>
            </div>

            {error && (
              <div className="issue-alert" role="alert">
                {error}
              </div>
            )}

            <button className="issue-button" type="submit">
              Validate credential information
            </button>

            <p className="issue-hint">
              Aucune émission n'est effectuée depuis cette page pour le moment.
              La signature et la persistance seront raccordées au véritable
              service backend.
            </p>
          </section>
        </form>
      </main>

      <Footer />
    </>
  );
}
