import { useState } from "react";
import { Link } from "react-router-dom";

import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import ProfileTabs from "../components/guide/ProfileTabs";
import { guideProfiles } from "../data/guide";
import "../styles/home.css";
import "../styles/guide.css";

const capabilities = [
  {
    number: "01",
    title: "Émettre",
    description:
      "Créez et émettez des justificatifs numériques signés à destination de leurs détenteurs.",
    detail: "Émission de justificatifs",
  },
  {
    number: "02",
    title: "Détenir",
    description:
      "Permettez aux détenteurs de conserver leurs justificatifs et de les présenter lorsqu'ils en ont besoin.",
    detail: "Wallet numérique",
  },
  {
    number: "03",
    title: "Vérifier",
    description:
      "Vérifiez indépendamment l'authenticité, l'émetteur et le statut d'un justificatif.",
    detail: "Vérification de justificatifs",
  },
];

function Home() {
  const [activeGuide, setActiveGuide] = useState(guideProfiles[0].id);
  const guideProfile =
    guideProfiles.find((item) => item.id === activeGuide) ||
    guideProfiles[0];

  return (
    <>
      <Navbar />

      <main>
        <section className="hero">
          <div className="hero-content">
            <span className="eyebrow">
              INFRASTRUCTURE D'IDENTITÉ NUMÉRIQUE
            </span>

            <h1>
              Votre identité.
              <br />
              <span>Vos justificatifs.</span>
              <br />
              Votre contrôle.
            </h1>

            <p className="hero-description">
              KeepYourID fournit l'infrastructure pour émettre, détenir et
              vérifier indépendamment des justificatifs numériques.
            </p>

            <div className="hero-actions">
              <a href="#product" className="button-primary">
                Explorer la plateforme <span>↗</span>
              </a>

              <a href="#technology" className="button-secondary">
                Découvrir le fonctionnement
              </a>
            </div>
          </div>

          <div className="hero-visual">
            <div className="visual-heading">
              <span>LE CYCLE DE VIE DU JUSTIFICATIF</span>
              <span className="live-indicator">●</span>
            </div>

            <div className="credential-card">
              <div className="credential-top">
                <span>JUSTIFICATIF VÉRIFIABLE</span>
                <span className="credential-mark">KY</span>
              </div>

              <div className="credential-icon">ID</div>

              <h3>Identité numérique</h3>
              <p>Un justificatif que vous pouvez vérifier.</p>

              <div className="credential-bottom">
                <span>ÉMIS PAR UNE ORGANISATION</span>
                <span>✓ SIGNÉ</span>
              </div>
            </div>

            <div className="visual-footer">
              <span>ÉMIS</span>
              <span>→</span>
              <span>DÉTENU</span>
              <span>→</span>
              <span>VÉRIFIÉ</span>
            </div>
          </div>
        </section>

        <section className="intro-section" id="product">
          <span className="eyebrow">UNE SEULE INFRASTRUCTURE</span>

          <div className="intro-heading">
            <h2>L'identité numérique, en pratique.</h2>

            <p>
              De l'organisation qui émet un justificatif à la personne
              qui le présente, KeepYourID relie les pièces essentielles
              de l'identité numérique.
            </p>
          </div>

          <div className="capabilities">
            {capabilities.map((item) => (
              <article className="capability" key={item.number}>
                <div className="capability-top">
                  <span>{item.number}</span>
                  <span>↗</span>
                </div>

                <div>
                  <span className="capability-detail">{item.detail}</span>
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="guide-teaser" id="guide">
          <div className="guide-teaser-header">
            <span className="eyebrow">PARCOURS GUIDÉS</span>
            <h2>Choisissez votre rôle, on vous guide.</h2>
            <p>
              Organisateur, titulaire ou vérificateur : chaque profil a son
              parcours pas à pas.
            </p>
          </div>

          <ProfileTabs
            profiles={guideProfiles}
            activeId={guideProfile.id}
            onChange={setActiveGuide}
          />

          <ol className="guide-teaser-steps">
            {guideProfile.steps.map((step, index) => (
              <li key={step.title}>
                <span className="guide-step-number">{index + 1}</span>
                <div>
                  <h3>{step.title}</h3>
                  <Link to={step.link.to} className="guide-step-link">
                    {step.link.label} <span>→</span>
                  </Link>
                </div>
              </li>
            ))}
          </ol>

          <Link to="/help" className="guide-teaser-cta">
            Voir le guide complet <span>↗</span>
          </Link>
        </section>

        <section className="technology-section" id="technology">
          <div>
            <span className="eyebrow">BASÉ SUR UNE CONFIANCE VÉRIFIABLE</span>
            <h2>La vérification ne doit pas dépendre d'une seule plateforme.</h2>
          </div>

          <p>
            Les justificatifs sont signés numériquement et conçus pour être
            vérifiés indépendamment. KeepYourID combine preuves
            cryptographiques, identité de l'émetteur et statut du
            justificatif pour rendre ce processus possible.
          </p>
        </section>

        <section className="cta-section" id="solutions">
          <span className="eyebrow">GARDEZ VOTRE IDENTITÉ SOUS CONTRÔLE</span>
          <h2>Bâtissez sur l'identité numérique vérifiable.</h2>
          <a href="/organizations/new" className="nav-button">
  Commencer <span>↗</span>
</a>
        </section>
      </main>

      <Footer />
    </>
  );
}

export default Home;