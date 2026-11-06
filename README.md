# KeepYourID

**Decentralized Digital Identity & Verifiable Credentials Platform**

KeepYourID est une plateforme d’identité numérique décentralisée fondée sur les principes du **Self-Sovereign Identity (SSI)**. Elle permet aux organisations d’émettre des attestations numériques signées cryptographiquement, aux individus de les conserver dans un wallet personnel et aux services tiers de vérifier ces attestations de manière indépendante.

> **Statut actuel :** MVP technique en cours. Les principaux composants backend, moteur de vérification et interface web de vérification sont implémentés. Le wallet mobile Expo reste à développer.

---

## 1. Membres du groupe

- **NGANDU KASEBA JOVIAL**
- **MONGA MBAKA EPHRAIM**

---

## 2. Objectifs du projet

- Permettre aux organisations de disposer d’une identité décentralisée (DID).
- Permettre l’émission d’attestations numériques signées cryptographiquement.
- Donner aux individus le contrôle de leurs attestations grâce à un wallet personnel.
- Permettre la présentation sélective d’informations afin de limiter la divulgation de données personnelles.
- Permettre à des services tiers de vérifier indépendamment l’authenticité et le statut des attestations.
- Mettre en place un mécanisme de révocation des credentials.

L’ambition est de construire un système dans lequel la confiance repose sur des mécanismes cryptographiques vérifiables, des identités décentralisées et des politiques de reconnaissance des émetteurs.

---

## 3. Architecture générale

KeepYourID adopte une architecture **modulaire**, organisée autour d’un backend métier FastAPI, d’un moteur de vérification indépendant et d’une application web React.

Le backend principal est un **Modular Monolith** : les responsabilités métier sont séparées par modules, mais partagent la même base applicative.

Le moteur de vérification est une frontière architecturale indépendante : il ne dépend ni de FastAPI, ni des modèles SQLAlchemy, ni des services métier du backend.

### 3.1 Vue d’ensemble

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

Le moteur de vérification fonctionne indépendamment du backend d’émission :

```text
         External Verifier
                |
                v
       Verification Engine
       keepyourid-verifier
                |
       +--------+---------+
       |        |         |
     DID     Signature  Credential
   Trust    Validation   Status
       |        |         |
       +--------+---------+
                |
        Verification Result
```

### 3.2 Composants principaux

#### Backend métier — `backend/`

Technologie : **Python 3.10+ / FastAPI / SQLAlchemy / PostgreSQL**.

Modules implémentés :

| Module | Responsabilité |
|---|---|
| `users` / `auth` | Inscription, login, logout, session utilisateur |
| `organizations` | Organisations, memberships et permissions |
| `dids` | DID organisations `did:ethr:sepolia`, challenges et vérification EIP-191 |
| `holders` | DID titulaires, challenges et credentials du wallet |
| `credentials` | Draft, émission, signature, status list Bitstring, révocation |
| `credential_verification` | API publique `POST /api/v1/verifications` adossée au moteur externe |
| `blockchain` | Adaptateur Ethereum, transactions et Issuer Registry |
| `health` | Healthcheck API |

Le backend expose une API sous `/api/v1` pour la plupart des routers. Le router `credentials` possède son propre prefix `/organizations/{organization_id}/credentials`; son inclusion exacte doit être vérifiée pour préserver la compatibilité des URLs de Status Lists déjà émises.

#### Verification Engine — `verification-engine/`

Package Python indépendant : **`keepyourid-verifier`**.

Responsabilités :

- Vérification de la signature EIP-191 du credential.
- Cohérence entre le signataire récupéré et le DID émetteur.
- Contrôle de confiance de l’émetteur via l’Issuer Registry blockchain.
- Contrôle d’expiration `validFrom` / `validUntil`.
- Contrôle de révocation via Status List Bitstring.

Entrée acceptée : enveloppe JSON `{"credential": {...}, "proof": {...}}` ou string JSON équivalente.

Sortie : `VerificationResult` avec `valid`, `credential_id`, `issuer`, `checks`, `errors`.

Configuration lue par le moteur : `ISSUER_REGISTRY_RPC_URL`, `ISSUER_REGISTRY_ADDRESS`.

#### Application web — `web/`

Technologie : **React 19 / Vite / React Router / Vitest / oxlint**.

Fonctionnalités implémentées :

- Authentification utilisateur.
- Portail organisations et memberships.
- Setup DID organisation.
- Wallet utilisateur avec connexion MetaMask sur Sepolia.
- Vérification DID titulaire par challenge signé.
- Liste des credentials du titulaire.
- QR code de présentation d’une credential.
- Copie du JSON `signed_credential`.
- Page publique `/verify` avec scan QR caméra et import JSON.
- Affichage détaillé des checks de vérification.

#### Wallet mobile — `wallet/`

Répertoire réservé pour l’application mobile. Technologie envisagée : **Expo / React Native**. Le wallet actuel est la page web `/wallet`.

---

## 4. Principes SSI

### 4.1 Decentralized Identifiers (DID)

Les organisations et les titulaires utilisent des DID `did:ethr:sepolia:<address>`. La preuve de contrôle se fait par challenge signé en EIP-191 et vérifié côté backend.

### 4.2 Verifiable Credentials (VC)

Les credentials sont des attestations numériques au format inspiré W3C VC v2, signées par l’émetteur. Le backend produit une enveloppe `{"credential": ..., "proof": ...}` stockée dans `signed_credential`.

### 4.3 Révocation

Le projet utilise le standard **Bitstring Status List**. Les credentials émis référencent une Status List signée publiée par le backend. Le moteur de vérification récupère cette Status List pour contrôler le bit de révocation.

### 4.4 Gestion des clés

Deux catégories de clés sont distinguées :

- **Clés émetteur** : signature des credentials et Status Lists.
- **Clés titulaire** : contrôle du DID holder via MetaMask / EIP-191.

Les clés privées ne doivent jamais être publiées.

---

## 5. Technologies

| Domaine | Technologie |
|---|---|
| Backend | Python 3.10+, FastAPI, SQLAlchemy, Alembic |
| Base de données | PostgreSQL via `psycopg` |
| Blockchain | Ethereum Sepolia / Anvil, `web3`, `eth-account` |
| DID method | `did:ethr` |
| Signature | EIP-191 personal signature |
| Credentials | W3C VC v2 inspiré, enveloppe `credential` + `proof` |
| Révocation | Bitstring Status List |
| Moteur de vérification | Package Python `keepyourid-verifier` |
| Frontend | React 19, Vite, React Router |
| Tests frontend | Vitest, Testing Library, jsdom |
| Lint frontend | oxlint |
| Mobile prévu | Expo / React Native |
| Conteneurs | Docker Compose pour PostgreSQL |

---

## 6. Installation et exécution

### Prérequis

- Python 3.10+.
- Node.js 20+.
- Git.
- Docker Compose pour PostgreSQL.
- MetaMask pour les tests wallet sur Sepolia.

### Base de données

```bash
docker compose up -d postgres
```

PostgreSQL est exposé sur le port `5434`.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
```

La dépendance `keepyourid-verifier` est déclarée dans `backend/pyproject.toml` via `file:../verification-engine` pour le développement local. `backend/requirements.txt` contient aussi une entrée VCS pinnée pour un déploiement reproductible.

Lancer l’API :

```bash
cd backend
./.venv/bin/uvicorn keepyourid.main:app --reload
```

API et documentation :

```text
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/docs
```

Tests backend ciblés :

```bash
cd backend
./.venv/bin/pytest -q tests/modules/credential_verification
./.venv/bin/ruff check src/keepyourid/modules/credential_verification tests/modules/credential_verification
```

### Moteur de vérification

```bash
cd verification-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

### Frontend

```bash
cd web
npm install
npm run dev
```

Si `npm install` échoue sur la résolution des peer dependencies, utiliser :

```bash
npm install --legacy-peer-deps
```

Lancer les tests et le build :

```bash
cd web
npm test
npm run lint
npm run build
```

Frontend par défaut : `http://localhost:5173`.

---

## 7. API principale

Préfixe global prévu : `/api/v1`.

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/api/v1/health` | Healthcheck |
| `POST` | `/api/v1/auth/register` | Inscription utilisateur |
| `POST` | `/api/v1/auth/login` | Login |
| `POST` | `/api/v1/auth/logout` | Logout |
| `GET` | `/api/v1/auth/me` | Utilisateur courant |
| `GET/POST` | `/api/v1/organizations` | Organisations |
| `GET/PATCH/DELETE` | `/api/v1/organizations/{id}/members...` | Memberships |
| `GET/POST` | `/api/v1/dids/...` | DID organisations, challenges, vérification |
| `GET/POST` | `/api/v1/holders/me/...` | DID titulaires, challenges, credentials |
| `POST` | `/api/v1/verifications` | Vérification d’une credential signée |
| `GET` | `/organizations/{organization_id}/credentials...` | Cycle de vie credentials et Status Lists |

### `POST /api/v1/verifications`

Requête :

```json
{
  "signed_credential": {
    "credential": {},
    "proof": {}
  }
}
```

`signed_credential` peut aussi être une string JSON.

Réponse `200` :

```json
{
  "valid": false,
  "credential_id": "urn:uuid:...",
  "issuer": "did:ethr:sepolia:0x...",
  "checks": {
    "signature": true,
    "issuer_did": true,
    "issuer_trust": false,
    "revocation": true,
    "expiration": true
  },
  "errors": ["Issuer is not registered."]
}
```

Codes : `200` vérification exécutée, `422` entrée invalide, `429` rate limit, `500` erreur technique.

---

## 8. Flux fonctionnel principal

1. Une organisation s’inscrit et est validée.
2. L’organisation crée et vérifie son DID `did:ethr:sepolia`.
3. L’organisation crée un credential, prépare l’émission, signe le credential et la Status List, puis termine l’émission.
4. Le credential émis est stocké avec `signed_credential = {"credential": ..., "proof": ...}`.
5. Le titulaire se connecte via MetaMask Sepolia, vérifie son Holder DID, puis consulte ses credentials dans `/wallet`.
6. Le titulaire affiche le QR code ou copie le JSON `signed_credential`.
7. Le vérificateur ouvre `/verify`, scanne le QR ou importe le JSON, puis appelle `POST /api/v1/verifications`.
8. L’interface affiche le verdict global, le credential ID, l’émetteur, chaque check et les erreurs.

---

## 9. Sécurité implémentée

- Le moteur de vérification reste indépendant du backend.
- Les destinations `statusListCredential` sont filtrées par allowlist : `CREDENTIAL_STATUS_LIST_ALLOWED_HOSTS`.
- La taille du payload `signed_credential` est limitée côté API.
- Un rate limit en mémoire est appliqué sur `/api/v1/verifications`.
- Les erreurs 500 ne exposent pas de stack trace.
- Les clés privées ne sont pas exposées côté frontend.

---

## 10. État actuel du projet

| Élément | État |
|---|---|
| Vision et objectifs | Définis |
| Architecture modulaire | Implémentée |
| Backend FastAPI | Fonctionnel sur les modules principaux |
| Auth utilisateurs | Implémentée |
| Organisations et memberships | Implémentés |
| DID organisations | Implémentés avec challenge EIP-191 |
| Holder wallet web | Implémenté avec MetaMask Sepolia |
| Émission credentials | Implémentée côté backend |
| Status Lists / révocation | Implémentées côté backend |
| Moteur de vérification | Implémenté comme package indépendant |
| API de vérification | `POST /api/v1/verifications` implémentée |
| Interface web vérification | `/verify` implémentée : QR caméra + import JSON |
| QR wallet + copie JSON | Implémentés |
| Tests frontend | 30 tests passent |
| Tests backend vérification | 16 tests passent |
| Mobile Expo | À développer |
| Présentation sélective | À développer |
| Déploiement production | À définir |

---

## 11. Points de vigilance

- Le router `credentials` doit être aligné avec le préfixe `/api/v1` sans casser les URLs de Status Lists déjà émises.
- Le moteur lit `ISSUER_REGISTRY_RPC_URL` / `ISSUER_REGISTRY_ADDRESS`; le backend utilise aussi `BLOCKCHAIN_RPC_URL` / `ISSUER_REGISTRY_ADDRESS`. L’alignement de configuration doit être vérifié pour `issuer_trust`.
- Le check `issuer_trust` du moteur utilise actuellement une chaîne cible à confirmer pour Sepolia/Anvil.
- La caméra du scanner QR nécessite un contexte sécurisé : `localhost` ou HTTPS.
- `CREDENTIAL_STATUS_LIST_ALLOWED_HOSTS` doit contenir l’hôte réel des Status Lists, sinon le check `revocation` est refusé côté API.
- La suite backend complète contient encore des échecs de tests liés à l’émission existante ; ils ne concernent pas le module `credential_verification`.

---

## 12. Dépôt

```text
keepyourid/
│
├── backend/
│   ├── src/keepyourid/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── modules/
│   │   │   ├── users/
│   │   │   ├── organizations/
│   │   │   ├── dids/
│   │   │   ├── holders/
│   │   │   ├── credentials/
│   │   │   ├── credential_verification/
│   │   │   └── health/
│   │   ├── verification/
│   │   └── blockchain/
│   ├── tests/
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── .env.example
│
├── verification-engine/
│   ├── src/keepyourid_verifier/
│   │   ├── engine.py
│   │   └── checks/
│   └── tests/
│
├── web/
│   ├── src/pages/
│   ├── src/components/
│   ├── src/services/
│   └── package.json
│
├── wallet/                 # réservé Expo / React Native
├── docker/
├── docker-compose.yml
├── docs/
└── README.md
```

---

## 13. Licence

La licence du projet reste à définir.

---

**KeepYourID — Decentralized Identity. Verifiable Trust.**
