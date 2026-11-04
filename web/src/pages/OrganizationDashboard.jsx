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
        <main className="dashboard-loading">Loading workspace...</main>
        <Footer />
      </>
    );
  }

  if (error || !organization) {
    return (
      <>
        <Navbar />
        <main className="dashboard-error">
          <h2>Unable to load workspace</h2>
          <p>{error || "The organization could not be loaded."}</p>
          <Link to="/organizations">Return to organizations</Link>
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
      type: "DID registration",
      label: did.identifier || "DID",
      date: did.created_at || did.updated_at,
      status: did.status,
    })),
    ...credentials.map((credential) => ({
      type: credential.status === "REVOKED" ? "Credential revocation" : "Credential issuance",
      label:
        credential.credential_type ||
        credential.type ||
        credential.credential_id ||
        "Verifiable credential",
      date: credential.created_at || credential.issued_at,
      status: credential.status,
    })),
    ...transactions.map((transaction) => ({
      type: transaction.operation || "Blockchain operation",
      label: transaction.transaction_hash || "Transaction recorded",
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
            <span className="eyebrow">ISSUER DASHBOARD</span>
            <h1>{organization.legal_name}</h1>
            <p>
              Monitor your credential issuance, digital identity and recent
              issuer operations.
            </p>
          </div>

          <Status value={organization.status} />
        </header>

        <section className="dashboard-metrics" aria-label="Overview statistics">
          <Metric
            label="Total credentials issued"
            value={totalCredentials}
            description="All credentials created"
          />
          <Metric
            label="Active credentials"
            value={activeCredentials}
            description="Currently in use"
          />
          <Metric
            label="Revoked credentials"
            value={revokedCredentials}
            description="Revoked from circulation"
          />
          <Metric
            label="Registered DIDs"
            value={registeredDids}
            description="Linked issuer identities"
          />
        </section>

        <section className="dashboard-actions" aria-label="Quick actions">
          <button type="button" className="dashboard-action dashboard-action--active" disabled>
            Issue a new credential
            <span>Coming soon</span>
          </button>

          <a className="dashboard-action" href="#issued-credentials">
            View issued credentials
          </a>

          <Link   to={`/organizations/${organizationId}/identity`}>
            Manage issuer DIDs
          </Link>

<Link className="dashboard-action"  to={`/organizations/${organizationId}/credentials`}>
  Gérer les justificatifs
</Link>
		  

          <button type="button" className="dashboard-action dashboard-action--muted" disabled>
            View revocation records
            <span>Coming soon</span>
          </button>
        </section>

        <section className="dashboard-grid">
          <article className="dashboard-panel dashboard-panel--wide">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">ACTIVITY</span>
                <h2>Recent activity</h2>
              </div>
            </div>

            {recentActivity.length === 0 ? (
              <div className="empty-state">
                <h3>No issuer activity yet</h3>
                <p>Once credentials or DIDs are created, they will appear here.</p>
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
                <span className="eyebrow">CREDENTIALS</span>
                <h2>Credential overview</h2>
              </div>
            </div>

            {credentials.length === 0 ? (
              <div className="empty-state">
                <h3>No credentials issued yet</h3>
                <p>Your recent credential history will appear here.</p>
              </div>
            ) : (
              <ul className="credential-list">
                {credentials.slice(0, 5).map((credential) => {
                  const holder =
                    credential.holder_did ||
                    credential.holder_id ||
                    credential.subject?.id ||
                    credential.credential_subject?.id ||
                    "Unknown holder";

                  return (
                    <li key={credential.id} className="credential-item">
                      <div className="credential-main">
                        <strong>{credential.credential_type || "Verifiable credential"}</strong>
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
