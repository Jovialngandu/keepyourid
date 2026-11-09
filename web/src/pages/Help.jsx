import { useState } from "react";
import { Link } from "react-router-dom";

import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import ProfileTabs from "../components/guide/ProfileTabs";
import { guideProfiles } from "../data/guide";

import "../styles/guide.css";

export default function Help() {
  const [activeProfile, setActiveProfile] = useState(guideProfiles[0].id);
  const profile =
    guideProfiles.find((item) => item.id === activeProfile) ||
    guideProfiles[0];

  return (
    <>
      <Navbar />

      <main className="guide-page">
        <header className="guide-header">
          <span className="eyebrow">GUIDE DE DÉMARRAGE</span>
          <h1>Comment utiliser KeepYourID ?</h1>
          <p>
            Choisissez votre profil pour suivre le parcours pas à pas, de la
            création du compte à la vérification d'un justificatif.
          </p>
        </header>

        <ProfileTabs
          profiles={guideProfiles}
          activeId={profile.id}
          onChange={setActiveProfile}
        />

        <section className="guide-panel">
          <div className="guide-panel-header">
            <h2>
              {profile.label}
            </h2>
            <p>{profile.tagline}</p>
          </div>

          <ol className="guide-steps">
            {profile.steps.map((step, index) => (
              <li className="guide-step" key={step.title}>
                <span className="guide-step-number">{index + 1}</span>

                <div className="guide-step-content">
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                  <Link
                    to={step.link.to}
                    className="guide-step-link"
                  >
                    {step.link.label} <span>→</span>
                  </Link>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <Footer />
    </>
  );
}
