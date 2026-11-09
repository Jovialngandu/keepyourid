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
    title: "Issue",
    description:
      "Créez et émettez des justificatifs numériques signés à destination de leurs détenteurs.",
    detail: "Credential issuance",
  },
  {
    number: "02",
    title: "Hold",
    description:
      "Permettez aux détenteurs de conserver leurs justificatifs et de les présenter lorsqu'ils en ont besoin.",
    detail: "Digital wallet",
  },
  {
    number: "03",
    title: "Verify",
    description:
      "Vérifiez indépendamment l'authenticité, l'émetteur et le statut d'un justificatif.",
    detail: "Credential verification",
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
              DIGITAL IDENTITY INFRASTRUCTURE
            </span>

            <h1>
              Your identity.
              <br />
              <span>Your credentials.</span>
              <br />
              Your control.
            </h1>

            <p className="hero-description">
              KeepYourID provides the infrastructure to issue, hold and
              independently verify digital credentials.
            </p>

            <div className="hero-actions">
              <a href="#product" className="button-primary">
                Explore the platform <span>↗</span>
              </a>

              <a href="#technology" className="button-secondary">
                Discover how it works
              </a>
            </div>
          </div>

          <div className="hero-visual">
            <div className="visual-heading">
              <span>THE CREDENTIAL LIFECYCLE</span>
              <span className="live-indicator">●</span>
            </div>

            <div className="credential-card">
              <div className="credential-top">
                <span>VERIFIABLE CREDENTIAL</span>
                <span className="credential-mark">KY</span>
              </div>

              <div className="credential-icon">ID</div>

              <h3>Digital identity</h3>
              <p>A credential you can verify.</p>

              <div className="credential-bottom">
                <span>ISSUED BY AN ORGANIZATION</span>
                <span>✓ SIGNED</span>
              </div>
            </div>

            <div className="visual-footer">
              <span>ISSUED</span>
              <span>→</span>
              <span>HELD</span>
              <span>→</span>
              <span>VERIFIED</span>
            </div>
          </div>
        </section>

        <section className="intro-section" id="product">
          <span className="eyebrow">ONE INFRASTRUCTURE</span>

          <div className="intro-heading">
            <h2>Digital identity, made practical.</h2>

            <p>
              From the organization issuing a credential to the person
              presenting it, KeepYourID connects the essential parts of
              digital identity.
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
            <span className="eyebrow">BUILT ON VERIFIABLE TRUST</span>
            <h2>Verification should not depend on a single platform.</h2>
          </div>

          <p>
            Credentials are digitally signed and designed to be verified
            independently. KeepYourID combines cryptographic proofs,
            issuer identity and credential status to support that process.
          </p>
        </section>

        <section className="cta-section" id="solutions">
          <span className="eyebrow">KEEP YOUR IDENTITY IN CONTROL</span>
          <h2>Build on verifiable digital identity.</h2>
          <a href="/organizations/new" className="nav-button">
  Get started <span>↗</span>
</a>
        </section>
      </main>

      <Footer />
    </>
  );
}

export default Home;