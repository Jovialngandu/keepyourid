
import { Link, useParams } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import "../styles/credentials.css";

export default function CredentialDetails() {
  const { organizationId, credentialId } = useParams();

  return (
    <>
      <Navbar />

      <main className="credentials-page">
        <header className="credentials-header">
          <Link to={`/organizations/${organizationId}/credentials`}>
            ← Retour aux credentials
          </Link>

          <span className="credentials-eyebrow">
            CREDENTIAL DETAILS
          </span>

          <h1>Credential details.</h1>
          <p>
            Consulte les informations et le statut de cette
            attestation numérique.
          </p>
        </header>

        <section className="credentials-card">
          <div className="credential-detail-heading">
            <div>
              <span className="credentials-eyebrow">
                CREDENTIAL IDENTIFIER
              </span>
              <h2>{credentialId}</h2>
            </div>
            <span className="credential-status pending">
              Awaiting API data
            </span>
          </div>

          <div className="credential-detail-section">
            <h3>Credential information</h3>
            <p>
              Les informations du credential seront chargées depuis
              le backend.
            </p>
          </div>

          <div className="credential-detail-section">
            <h3>Holder</h3>
            <p>DID du détenteur : non chargé</p>
          </div>

          <div className="credential-detail-section">
            <h3>Issuer</h3>
            <p>Identité de l'émetteur : non chargée</p>
          </div>

          <div className="credential-detail-section">
            <h3>Cryptographic verification</h3>
            <p>
              La signature et le statut devront être vérifiés
              à partir des données réelles du credential.
            </p>
          </div>

          <div className="credential-detail-section">
            <h3>Lifecycle</h3>
            <p>
              Les opérations disponibles dépendront du statut réel
              et des permissions de l'émetteur.
            </p>
          </div>

          <p className="credentials-api-notice">
            Cette page ne prétend pas avoir vérifié ou chargé
            le credential. Le raccordement API reste à effectuer.
          </p>
        </section>
      </main>

      <Footer />
    </>
  );
}
