import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import {
  getOrganization,
  getOrganizationDids,
  getOrganizationCredentials,
  getOrganizationTransactions,
} from "../services/organization";

import "../styles/organization-dashboard.css";

function Status({ value }) {
  const status = value || "UNKNOWN";

  const colors = {
    ACTIVE: "success",
    VERIFIED: "success",
    CONFIRMED: "success",
    ISSUED: "success",
    PENDING: "pending",
    REGISTERED: "pending",
    REVOKED: "danger",
    FAILED: "danger",
    SUSPENDED: "danger",
  };

  return (
    <span className={`status status-${colors[status] || "neutral"}`}>
      {status}
    </span>
  );
}

function Metric({ label, value, description }) {
  return (
    <div className="dashboard-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{description}</small>
    </div>
  );
}

function formatDate(dateValue) {
  if (!dateValue) return "—";

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) return "—";

  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

export default function OrganizationDashboard() {
  const { organizationId } = useParams();

  const [organization, setOrganization] = useState(null);
  const [dids, setDids] = useState([]);
  const [credentials, setCredentials] = useState([]);
  const [transactions, setTransactions] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const org = await getOrganization(organizationId);

        if (cancelled) return;

        setOrganization(org);

        const results = await Promise.allSettled([
          getOrganizationDids(organizationId),
          getOrganizationCredentials(organizationId),
          getOrganizationTransactions(organizationId),
        ]);

        if (cancelled) return;

        if (results[0].status === "fulfilled") {
          const didResult = results[0].value;
          setDids(Array.isArray(didResult) ? didResult : didResult?.items || []);
        }

        if (results[1].status === "fulfilled") {
          const data = results[1].value;
          setCredentials(Array.isArray(data) ? data : data?.items || []);
        }

        if (results[2].status === "fulfilled") {
          const data = results[2].value;
          setTransactions(Array.isArray(data) ? data : data?.items || []);
        }
      } catch (err) {
        if (!cancelled) setError(err.message || "Unable to load organization data.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [organizationId]);

  if (loading) {
    return (
      <>
        <Navbar />
        <main className="dashboard-loading">Chargement de l'espace...</main>
        <Footer />
      </>
    );
  }

  if (error || !organization) {
    return (
      <>
        <Navbar />
        <main className="dashboard-error">
          <h2>Impossible de charger l'espace</h2>
          <p>{error || "L'organisation n'a pas pu être chargée."}</p>
          <Link to="/organizations">Retour aux organisations</Link>
        </main>
        <Footer />
      </>
    );
  }

  const totalCredentials = credentials.length;
  const activeCredentials = credentials.filter((credential) => {
    const status = String(credential.status || "").toUpperCase();
    return ["ACTIVE", "ISSUED", "VERIFIED", "CONFIRMED"].includes(status);
  }).length;
  const revokedCredentials = credentials.filter((credential) => {
    const status = String(credential.status || "").toUpperCase();
    return status === "REVOKED";
  }).length;
  const registeredDids = dids.length;

  const recentActivity = [
    ...dids.map((did) => ({
      type: "Enregistrement de DID",
      label: did.identifier || "DID",
      date: did.created_at || did.updated_at,
      status: did.status,
    })),
    ...credentials.map((credential) => ({
      type: credential.status === "REVOKED" ? "Révocation de justificatif" : "Émission de justificatif",
      label:
        credential.credential_type ||
        credential.type ||
        credential.credential_id ||
        "Justificatif vérifiable",
      date: credential.created_at || credential.issued_at,
      status: credential.status,
    })),
    ...transactions.map((transaction) => ({
      type: transaction.operation || "Opération blockchain",
      label: transaction.transaction_hash || "Transaction enregistrée",
      date: transaction.created_at || transaction.updated_at,
      status: transaction.status,
    })),
  ]
    .sort((first, second) => new Date(second.date || 0) - new Date(first.date || 0))
    .slice(0, 6);

  return (
    <>
      <Navbar />

      <main className="organization-dashboard">
        <header className="dashboard-header">
          <div>
            <span className="eyebrow">TABLEAU DE BORD ÉMETTEUR</span>
            <h1>{organization.legal_name}</h1>
            <p>
              Suivez l'émission de vos justificatifs, votre identité
              numérique et vos dernières opérations.
            </p>
          </div>

          <Status value={organization.status} />
        </header>

        <section className="dashboard-metrics" aria-label="Overview statistics">
          <Metric
            label="Total des justificatifs émis"
            value={totalCredentials}
            description="Tous les justificatifs créés"
          />
          <Metric
            label="Justificatifs actifs"
            value={activeCredentials}
            description="Actuellement utilisés"
          />
          <Metric
            label="Justificatifs révoqués"
            value={revokedCredentials}
            description="Retirés de la circulation"
          />
          <Metric
            label="DID enregistrés"
            value={registeredDids}
            description="Identités d'émetteur liées"
          />
        </section>

        <section className="dashboard-actions" aria-label="Actions rapides">
          <Link
            className="dashboard-action dashboard-action--active"
            to={`/organizations/${organizationId}/credentials`}
          >
            Émettre un justificatif
          </Link>

          <Link
            className="dashboard-action"
            to={`/organizations/${organizationId}/identity`}
          >
            Gérer les DID émetteurs
          </Link>

          <a className="dashboard-action" href="#issued-credentials">
            Voir les justificatifs émis
          </a>

          <Link
            className="dashboard-action"
            to={`/organizations/${organizationId}/credentials`}
          >
            Gérer les justificatifs
          </Link>
        </section>

        <section className="dashboard-grid">
          <article className="dashboard-panel dashboard-panel--wide">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">ACTIVITÉ</span>
                <h2>Activité récente</h2>
              </div>
            </div>

            {recentActivity.length === 0 ? (
              <div className="empty-state">
                <h3>Aucune activité d'émission pour le moment</h3>
                <p>Une fois des justificatifs ou des DID créés, ils apparaîtront ici.</p>
              </div>
            ) : (
              <ul className="activity-list">
                {recentActivity.map((entry, index) => (
                  <li key={`${entry.type}-${entry.label}-${index}`} className="activity-item">
                    <div>
                      <strong>{entry.type}</strong>
                      <small>{entry.label}</small>
                    </div>

                    <div className="activity-meta">
                      <span>{formatDate(entry.date)}</span>
                      {entry.status ? <Status value={entry.status} /> : null}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article id="issued-credentials" className="dashboard-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">JUSTIFICATIFS</span>
                <h2>Vue d'ensemble des justificatifs</h2>
              </div>
            </div>

            {credentials.length === 0 ? (
              <div className="empty-state">
                <h3>Aucun justificatif émis pour le moment</h3>
                <p>Votre historique récent de justificatifs apparaîtra ici.</p>
              </div>
            ) : (
              <ul className="credential-list">
                {credentials.slice(0, 5).map((credential) => {
                  const holder =
                    credential.holder_did ||
                    credential.holder_id ||
                    credential.subject?.id ||
                    credential.credential_subject?.id ||
                    "Titulaire inconnu";

                  return (
                    <li key={credential.id} className="credential-item">
                      <div className="credential-main">
                        <strong>{credential.credential_type || "Justificatif vérifiable"}</strong>
                        <small>{holder}</small>
                      </div>

                      <div className="credential-meta">
                        <span>{formatDate(credential.created_at || credential.issued_at)}</span>
                        <Status value={credential.status} />
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </article>
        </section>
      </main>

      <Footer />
    </>
  );
}
