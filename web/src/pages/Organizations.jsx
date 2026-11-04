
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "../services/api";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import "../styles/organization.css";
import "../styles/organization-register.css";


function Organizations() {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadOrganizations() {
      try {
        const result = await apiRequest("/organizations/");
        setOrganizations(result.items || []);
      } catch (err) {
        setError(err.message || "Impossible de charger les organisations.");
      } finally {
        setLoading(false);
      }
    }

    loadOrganizations();
  }, []);

  return (
    <>
      <Navbar />

      <main className="organizations-page">
        <section className="organizations-header">
          <div>
            <span className="eyebrow">WORKSPACE</span>
            <h1>Mes organisations</h1>
            <p>
              Gérez vos organisations, leurs identités décentralisées et
              leurs credentials.
            </p>
          </div>

          <Link to="/organizations/new" className="primary-button">
            <span>+</span> Nouvelle organisation
          </Link>
        </section>

        {loading ? (
          <div className="organizations-loading">
            Chargement des organisations...
          </div>
        ) : error ? (
          <div className="organizations-error">{error}</div>
        ) : organizations.length === 0 ? (
          <section className="organizations-empty">
            <div className="empty-icon">◇</div>
            <h2>Aucune organisation pour le moment</h2>
            <p>
              Créez votre première organisation pour commencer à gérer
              votre identité et vos credentials.
            </p>
            <Link to="/organizations/new" className="primary-button">
              Créer une organisation
            </Link>
          </section>
        ) : (
          <section className="organizations-grid">
            {organizations.map((organization) => (
              <article className="organization-card" key={organization.id}>
                <div className="organization-card-top">
                  <div className="organization-icon">◇</div>
                  <span
                    className={`organization-status status-${organization.status?.toLowerCase()}`}
                  >
                    {organization.status}
                  </span>
                </div>

                <h2>{organization.legal_name}</h2>
                <p>{organization.email}</p>

                <div className="organization-card-footer">
                  <span>
                    N° {organization.registration_number}
                  </span>
                  <Link to={`/organizations/${organization.id}`}>
                    Ouvrir <span>↗</span>
                  </Link>
                </div>
              </article>
            ))}
          </section>
        )}
      </main>

      <Footer />
    </>
  );
}

export default Organizations;
