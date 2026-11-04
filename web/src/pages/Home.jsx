import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import "../styles/home.css";

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