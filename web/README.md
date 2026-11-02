# KeepYourID — Frontend Angular

Frontend local dans le dépôt principal. Angular 21 standalone, Tailwind CSS, TypeScript strict, Router, formulaires réactifs, HttpClient et tests Vitest. Node 22.20 est compatible avec Angular 21 ; Angular 22 demande une version Node plus récente.

## Styles Tailwind

Tailwind est intégré via le plugin officiel `@tailwindcss/postcss` dans `.postcssrc.json`. Les couleurs KeepYourID et les polices sont déclarées dans `@theme` dans `src/styles.css` : utiliser par exemple `bg-ink`, `text-muted`, `bg-brand` ou `font-heading` dans les templates.

Les styles existants sont dans la couche `components`, ce qui permet aux classes utilitaires Tailwind de les surcharger. Les boutons, les groupes d’actions et les grilles utilisent aussi `@apply`. Le reset Preflight est volontairement omis pour conserver les styles de base et le rendu existant. Les imports `theme.css` et `utilities.css` permettent d’utiliser Tailwind sans ce reset. Référence : [installation Angular](https://tailwindcss.com/docs/installation/framework-guides/angular).

## Démarrer

```powershell
cd web
npm ci
npm start
```

Ouvrir http://localhost:4200. Le proxy de développement transmet `/api` vers `http://127.0.0.1:8000`. Démarrer séparément FastAPI et PostgreSQL selon le README principal. Adapter `proxy.conf.json` si le port backend diffère.

```powershell
npm run build
npm test -- --watch=false
```

La sortie statique est dans `dist/keepyourid-web/browser`. L’hébergement doit renvoyer `index.html` pour les routes Angular, servir `config.json` sans cache et router `/api` vers FastAPI, ou configurer CORS côté API pour une origine distincte.

## Configuration et accès

`public/config.json`, copié à la racine du build, contient les seuls paramètres publics :

```json
{ "apiBaseUrl": "/api/v1", "workspaceEnabled": false }
```

Utiliser un fichier différent par environnement : local, staging et production. L’URL peut être absolue ou relative. Aucun secret n’y est autorisé.

Le portail est **fermé par défaut** et redirige vers `/login`. Le backend ne dispose pas encore d’authentification : aucune connexion fictive, aucun token inventé. Pour une intégration locale avec une API de développement, mettre explicitement `workspaceEnabled` à `true`, puis recharger. Cela ouvre les outils d’intégration, **sans authentifier ni autoriser un utilisateur**. Ne pas activer sur un environnement public. Avant production, intégrer une session réelle et les contrôles de permissions côté serveur.

## Routes

- Public : `/`, `/about`, `/how-it-works`, `/organizations`, `/wallet`, `/verification`, `/standards`, `/contact`.
- Accès : `/login`, `/register`.
- Portail local : `/issuer/dashboard`, `/issuer/credentials`, `/issuer/issue`, `/issuer/credentials/:id`, `/issuer/did`, `/verifier`, `/admin`.

Le wallet est présenté comme un futur produit mobile distinct. Aucun wallet web ou compte de démonstration n’est créé. Le tableau de bord réutilise la liste et les compteurs calculés sur les réponses réelles du serveur.

## API utilisées

Préfixe configurable, par défaut `/api/v1`.

| Méthode   | Route                                                                            | Usage                                    |
| --------- | -------------------------------------------------------------------------------- | ---------------------------------------- |
| GET       | `/health`                                                                        | Disponibilité HTTP de l’API              |
| POST      | `/organizations/`                                                                | Inscription                              |
| POST      | `/dids/organizations/{organization_id}`                                          | Enregistrement DID                       |
| POST      | `/dids/{did_id}/challenges`                                                      | Challenge à signer dans un outil externe |
| POST      | `/dids/{did_id}/verify`                                                          | Preuve de contrôle                       |
| GET, POST | `/organizations/{organization_id}/credentials`                                   | Liste, création                          |
| GET       | `/organizations/{organization_id}/credentials/{credential_id}`                   | Détail                                   |
| POST      | `/organizations/{organization_id}/credentials/{credential_id}/prepare-issuance`  | Message et identifiant de clé            |
| POST      | `/organizations/{organization_id}/credentials/{credential_id}/complete-issuance` | Signature externe et finalisation        |

Le portail demande l’UUID d’organisation parce qu’il n’existe pas encore de session ou d’endpoint profil. Cet UUID est conservé uniquement en mémoire. Ni les attributs des credentials, ni les signatures, ni des tokens ne sont stockés dans localStorage/sessionStorage.

Pour émettre : charger une organisation active avec DID vérifié, créer le brouillon, préparer le message, le signer avec l’outil de l’organisation, coller la signature et confirmer. Aucune clé privée ne doit être saisie dans le navigateur. Le résultat est déclaré émis uniquement après réponse positive du backend. Le JWS peut alors être téléchargé.

## Limites liées au backend

- Authentification, autorisation et sessions non exposées.
- Inscription actuellement susceptible d’échouer : statut `PENDING` référencé par le service mais absent de l’énumération backend.
- Pas de moteur/API de vérification VC, révocation, présentations, scan QR, historique ou liste des émetteurs de confiance.
- Pas d’API de gestion administrative des comptes, registrars, transactions ou audits.
- Pas d’API GET profil organisation ; saisie explicite de l’UUID en intégration locale.
- Le détail credential ne renvoie pas le JWS signé : téléchargement disponible à la finalisation uniquement.
- Le healthcheck ne valide pas les dépendances PostgreSQL/blockchain.

Ces fonctions ne sont pas simulées. La supervision et la vérification affichent précisément leurs limites.

## Structure

`core/` : configuration, API, erreurs et contrôle d’accès local. `shared/` : modèles et contexte organisation. `layouts/` : site public et portail. `features/` : public, organisations, authentification, DID, credentials, vérification et administration.

Les tests couvrent les contrats HTTP, les erreurs serveur, le guard, les attributs JSON et la finalisation d’émission avec confirmation. Ils ne remplacent pas un test intégré avec le backend, la base et le résolveur DID.

Voir [l’analyse détaillée](../docs/frontend-analysis.md). Direction visuelle propre à KeepYourID, inspirée de la structure des parcours de [walt.id](https://walt.id/). Compatibilité de versions : [documentation Angular](https://angular.dev/reference/versions).
