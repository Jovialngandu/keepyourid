# KeepYourID

**Decentralized Digital Identity & Verifiable Credentials Platform**

KeepYourID est un projet de plateforme d'identité numérique décentralisée fondée sur les principes du **Self-Sovereign Identity (SSI)**. Son objectif est de permettre aux organisations d'émettre des attestations numériques vérifiables cryptographiquement, aux individus de les conserver dans leur propre portefeuille numérique et aux services tiers de vérifier ces attestations de manière indépendante.

Le projet vise à proposer une infrastructure permettant de réduire la dépendance à un intermédiaire central pour la vérification des identités et des justificatifs numériques.

> **Statut du projet :** Architecture initiale et mise en place du socle technique.

---

## 1. Membres du groupe

- **NGANDU KASEBA JOVIAL**
- **MONGA MBAKA EPHRAIM**

---

## 2. Objectifs du projet

KeepYourID poursuit les objectifs suivants :

- Permettre aux organisations de disposer d'une identité décentralisée (DID).
- Permettre l'émission d'attestations numériques signées cryptographiquement.
- Donner aux individus le contrôle de leurs attestations numériques grâce à un portefeuille personnel.
- Permettre la présentation sélective d'informations afin de limiter la divulgation de données personnelles.
- Permettre à des services tiers de vérifier indépendamment l'authenticité et le statut des attestations.
- Mettre en place un mécanisme de gestion de la révocation des credentials.

L'ambition est de construire un système dans lequel la confiance repose sur des mécanismes cryptographiques vérifiables, des identités décentralisées et des politiques de reconnaissance des émetteurs.

---

## 3. Architecture générale

KeepYourID adopte une architecture **modulaire**, organisée autour d'un backend métier et de composants indépendants.

Le backend principal est conçu comme un **Modular Monolith**. Cette approche permet de conserver une base applicative cohérente tout en séparant les responsabilités métier.

Le moteur de vérification constitue une frontière architecturale indépendante : il ne doit pas dépendre des services métier du backend KeepYourID.

### 3.1 Vue d'ensemble

```text
                 KEEPYOURID ECOSYSTEM
                          |
          +---------------+----------------+
          |               |                |
     Organization       Citizen         Verifier
       Portal            Wallet           Portal
          |               |                |
          +---------------+----------------+
                          |
                  KeepYourID Backend
                       FastAPI
                          |
       +------------------+------------------+
       |                  |                  |
  Organizations       Identity          Credentials
       |                  |                  |
  Onboarding            DID              Presentations
       |                  |                  |
  Members & Access      Trust              Status
       |                  |                  |
       +------------------+------------------+
                          |
                    Infrastructure
                          |
             +------------+------------+
             |            |            |
          Database    Cryptography  Blockchain
```

Le moteur de vérification est conçu pour fonctionner indépendamment du backend d'émission :

```text
         External Verifier
                |
                v
       Verification Engine
                |
       +--------+---------+
       |        |         |
     DID     Signature  Credential
   Resolver  Validation   Status
       |        |         |
       +--------+---------+
                |
        Verification Result
```

### 3.2 Composants principaux

#### Backend métier

Le backend centralise les opérations métier de la plateforme.

Technologie retenue : **Python + FastAPI**.

Il regroupe les responsabilités suivantes :

| Module | Responsabilité |
|---|---|
| Organizations | Inscription et gestion des organisations |
| Onboarding | Validation des organisations avant autorisation d'émission |
| Identity | Gestion des identités décentralisées |
| Members | Gestion des utilisateurs, agents et permissions |
| Credentials | Gestion et émission des attestations |
| Presentations | Gestion des demandes et présentations |
| Status | Révocation et suspension des attestations |
| Trust | Politiques de confiance et reconnaissance des émetteurs |

#### Verification Engine

Le moteur de vérification est un composant indépendant chargé de vérifier les credentials et les présentations.

Ses responsabilités comprennent :

- La résolution des DID.
- La vérification des signatures cryptographiques.
- Le contrôle de la validité des credentials.
- La vérification des statuts de révocation.
- L'application des politiques de confiance.
- La production d'un résultat de vérification structuré.

Il ne doit pas dépendre des modèles de données internes ni des services métier du backend principal.

#### Wallet citoyen

Le wallet est destiné aux individus.

Il permettra notamment de conserver les attestations numériques, de consulter leur contenu et de préparer des présentations à destination des services demandeurs.

Technologie envisagée : **Expo / React Native**.

#### Portail organisation

Le portail permettra aux organisations de rejoindre la plateforme, de configurer leur identité décentralisée, de gérer leurs agents et d'émettre des attestations.

L'inscription sera libre, mais une validation sera obligatoire avant toute émission.

#### Portail vérificateur

Le portail fournira une interface permettant de vérifier des présentations et des attestations.

La vérification sera également accessible par API afin de permettre l'intégration de services externes.

---

## 4. Principes SSI

### 4.1 Decentralized Identifiers (DID)

Les organisations disposent d'identifiants décentralisés permettant de retrouver les informations publiques nécessaires à la vérification de leur identité cryptographique.

Le DID method envisagé pour le premier prototype est `did:ethr`.

### 4.2 Verifiable Credentials (VC)

Les organisations émettent des attestations numériques signées cryptographiquement.

Un credential contient notamment :

- L'identité de l'émetteur.
- Les informations attestées.
- L'identité du titulaire, selon le modèle retenu.
- Les informations de validité.
- Les informations relatives à son statut.

### 4.3 Verifiable Presentations (VP)

Les individus peuvent présenter leurs credentials à des services tiers.

La présentation doit permettre de limiter les informations divulguées en fonction de la demande et du format cryptographique choisi.

### 4.4 Gestion des clés

Le système distingue deux catégories principales de clés :

- **Clés de l'émetteur :** utilisées pour signer les credentials.
- **Clés du titulaire :** utilisées par le wallet pour démontrer le contrôle de son identité ou participer aux mécanismes de présentation.

Les clés privées ne doivent jamais être publiées sur la blockchain.

### 4.5 Révocation

Le projet prévoit l'utilisation du standard W3C Bitstring Status List pour permettre aux vérificateurs de contrôler le statut des credentials.

---

## 5. Technologies

| Domaine | Technologie |
|---|---|
| Backend | Python |
| Framework API | FastAPI |
| Application mobile | Expo / React Native |
| Smart contracts | Solidity |
| Blockchain envisagée | Ethereum Sepolia |
| DID method envisagé | did:ethr |
| Base de données envisagée | PostgreSQL |
| Environnement Python | venv |
| Gestion des dépendances | pip |
| Tests backend | pytest |
| Documentation API | OpenAPI / Swagger |

Les bibliothèques spécialisées pour DID, VC, signatures et divulgation sélective feront l'objet d'une sélection technique en fonction de leur compatibilité avec les standards retenus.

---

## 6. Installation et exécution

### Prérequis

- Python 3.11 ou supérieur.
- pip.
- Git.

### Cloner le dépôt

```bash
git clone <repository-url>
cd keepyourid
```

### Initialiser l'environnement backend

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### Configurer les variables d'environnement

```bash
cp .env.example .env
```

### Lancer l'application

```bash
uvicorn keepyourid.main:app --reload
```

L'API sera accessible à l'adresse :

```text
http://127.0.0.1:8000
```

Documentation interactive :

```text
http://127.0.0.1:8000/docs
```

### Exécuter les tests

```bash
pytest -v
```

---

## 7. Architecture du dépôt

```text
keepyourid/
│
├── backend/
│   ├── src/
│   │   └── keepyourid/
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── modules/
│   │       └── infrastructure/
│   ├── tests/
│   └── pyproject.toml
│
├── verification-engine/
│
├── wallet/
│
├── web/
│
├── contracts/
│
├── docs/
│   └── architecture.md
│
├── .gitignore
└── README.md
```

Les répertoires représentent les frontières des composants envisagés. Leur contenu sera développé progressivement selon l'avancement du projet.

---

## 8. État actuel du projet

Le projet se trouve dans sa phase initiale.

| Élément | État |
|---|---|
| Vision et objectifs | Définis |
| Architecture générale | Définie initialement |
| Choix FastAPI | Retenu |
| Structure du dépôt | En initialisation |
| Backend | Socle initial |
| Module DID | À développer |
| Émission de credentials | À développer |
| Wallet | À développer |
| Moteur de vérification | À développer |
| Smart contracts | À développer |
| Révocation | À développer |

Les éléments indiqués comme « à développer » ne sont pas présentés comme des fonctionnalités déjà opérationnelles.

---

## 9. Adresses des contrats

Aucun contrat intelligent n'est actuellement déployé.

| Réseau | Adresse |
|---|---|
| Ethereum Sepolia | Non disponible — aucun déploiement effectué |

---

## 10. Déploiement

Aucun environnement de production ou de démonstration n'est actuellement configuré.

Les modalités de déploiement seront documentées après la mise en place et la validation des premiers composants.

---

## 11. Tests

Les tests automatisés seront développés progressivement.

Les principaux scénarios de validation prévus sont :

- Inscription et validation d'une organisation.
- Création et résolution d'un DID.
- Émission d'un credential signé.
- Vérification indépendante de la signature.
- Présentation d'un credential par son titulaire.
- Détection d'un credential révoqué.
- Rejet d'un credential invalide.

Le scénario central du MVP sera une chaîne complète allant de l'émission à la vérification indépendante.

---

## 12. Captures d'écran et démonstration

Les captures d'écran seront ajoutées au fur et à mesure de l'implémentation des interfaces.

Aucune capture ni aucun compte de démonstration n'est actuellement disponible.

---

## 13. Licence

La licence du projet reste à définir.

---

**KeepYourID — Decentralized Identity. Verifiable Trust.**