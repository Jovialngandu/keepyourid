# KeepYourID — Architecture technique

**Version :** 0.1  
**Statut :** Architecture initiale du MVP  
**Orientation :** Self-Sovereign Identity (SSI)

## 1. Vision technique

KeepYourID est une plateforme d'identité numérique décentralisée permettant aux organisations d'émettre des attestations numériques vérifiables cryptographiquement et aux individus de les conserver et de les présenter à des services tiers.

Le système doit permettre :

- Aux organisations de créer et gérer leur identité décentralisée.
- Aux organisations autorisées d'émettre des Verifiable Credentials.
- Aux individus de conserver leurs credentials dans leur propre wallet.
- Aux individus de présenter des informations avec un minimum de divulgation.
- Aux services tiers de vérifier indépendamment les présentations.
- Aux émetteurs de publier et gérer le statut de leurs credentials.

Le MVP vise à démontrer une chaîne complète d'émission, de conservation, de présentation et de vérification.

## 2. Principes architecturaux

### 2.1 Python-first

Le backend métier sera développé avec Python et FastAPI.

Les autres technologies seront choisies selon les besoins réels de chaque composant.

### 2.2 Modular monolith

Le backend métier sera initialement un monolithe modulaire.

Les modules partageront le même processus applicatif et la même infrastructure de déploiement, mais conserveront des responsabilités et des interfaces distinctes.

Aucun découpage en microservices n'est prévu pour le MVP.

### 2.3 Séparation des responsabilités

Les règles métier ne doivent pas dépendre directement des bibliothèques cryptographiques, des fournisseurs blockchain ou des mécanismes de stockage.

Les intégrations techniques seront isolées derrière des interfaces.

### 2.4 Vérification indépendante

Le moteur de vérification ne dépendra pas du backend métier KeepYourID.

Il devra pouvoir vérifier un credential ou une présentation à partir des éléments publics et des données nécessaires, sans interroger l'API d'émission.

### 2.5 Minimisation des données

Aucune donnée personnelle ni aucun credential complet ne sera inscrit sur la blockchain.

Les données personnelles seront conservées hors chaîne, sous le contrôle des acteurs qui en ont besoin.

## 3. Composants

### 3.1 Backend métier

Technologie principale : Python + FastAPI.

Modules :

- organizations : inscription et gestion des organisations.
- onboarding : validation et activation des organisations.
- identity : gestion des DID et résolution.
- members : utilisateurs, rôles et permissions.
- credentials : modèles, émission et signature.
- presentations : traitement des présentations.
- status : révocation et suspension.
- trust : politiques de confiance et reconnaissance des émetteurs.

### 3.2 Verification Engine

Package indépendant chargé de :

- Lire et interpréter les credentials et présentations supportés.
- Résoudre les DID.
- Vérifier les signatures.
- Vérifier les périodes de validité.
- Vérifier le statut des credentials.
- Appliquer une politique de confiance fournie par le vérificateur.
- Produire un résultat structuré.

Le moteur ne doit pas importer les modèles ORM ni les services métier du backend.

### 3.3 Wallet

Application mobile construite avec Expo et React Native.

Responsabilités :

- Gestion des clés du titulaire.
- Conservation locale des credentials.
- Réception des credentials.
- Préparation des présentations.
- Consentement avant divulgation.
- Sauvegarde et restauration chiffrées.

### 3.4 Smart contracts et registre DID

La blockchain servira principalement à l'enregistrement et à la résolution des identités décentralisées.

Le réseau de test envisagé est Ethereum Sepolia avec le DID method did:ethr.

Les signatures des credentials seront effectuées hors chaîne.

### 3.5 Interfaces Web

Le portail organisation permettra l'inscription, la configuration du DID, la gestion des agents et l'émission.

Le portail vérificateur permettra de vérifier des présentations.

L'administration centrale gérera l'accès à la plateforme et les validations d'organisations.

## 4. Flux métier fondamentaux

### 4.1 Inscription d'une organisation

1. Une organisation crée un compte.
2. Elle renseigne ses informations.
3. Elle configure son identité décentralisée.
4. Elle soumet les éléments nécessaires à sa validation.
5. KeepYourID examine la demande.
6. L'organisation devient autorisée à émettre après validation.

L'inscription et la configuration du DID sont libres, mais l'émission est conditionnée par la validation.

### 4.2 Émission d'un credential

1. Un agent autorisé sélectionne un type de credential.
2. Il fournit les informations nécessaires.
3. Le backend applique les règles métier.
4. Le service de signature utilise la clé de l'émetteur.
5. Le credential signé est remis au titulaire.
6. Son statut initial est publié selon le mécanisme retenu.

### 4.3 Présentation et vérification

1. Un vérificateur formule une demande.
2. Le wallet présente les informations autorisées par son titulaire.
3. Le moteur de vérification résout le DID de l'émetteur.
4. Il vérifie la signature et la validité.
5. Il contrôle le statut du credential.
6. Il applique sa propre politique de confiance.
7. Il retourne un résultat détaillé.

La vérification cryptographique et la décision de confiance sont deux opérations distinctes.

## 5. Sécurité et gestion des clés

- La clé privée de l'émetteur reste sous le contrôle de l'organisation.
- La clé privée du titulaire reste sous le contrôle de son wallet.
- Les clés privées ne sont jamais publiées sur la blockchain.
- Le backend ne doit pas devenir le dépositaire universel des clés des citoyens.
- Les opérations sensibles doivent être protégées par des permissions.
- Les mécanismes de rotation et de compromission des clés devront être prévus.

## 6. Standards et choix techniques

### Orientations retenues

- W3C Decentralized Identifiers (DID Core).
- W3C Verifiable Credentials Data Model 2.0.
- DID method envisagé : did:ethr.
- Ethereum Sepolia pour les premiers essais.
- W3C Bitstring Status List pour les statuts.
- Expo / React Native pour le wallet.

### Choix encore à valider par prototype

- Profil exact de sécurisation des credentials.
- Compatibilité des bibliothèques Python avec les standards sélectionnés.
- Mécanisme de divulgation sélective.
- Format des présentations.
- Bibliothèque et méthode de résolution DID.
- Format et procédure de récupération du wallet.

Le choix du modèle VC et de son mécanisme cryptographique devra être cohérent. W3C VC Data Model 2.0 et SD-JWT VC ne sont pas interchangeables.

## 7. Critères de validation du MVP

Le MVP sera considéré comme techniquement validé lorsque :

1. Une organisation pourra s'inscrire.
2. Elle pourra configurer son DID.
3. Elle pourra être validée avant émission.
4. Elle pourra émettre un credential signé.
5. Un wallet pourra le conserver.
6. Le titulaire pourra le présenter.
7. Un vérificateur indépendant pourra le vérifier.
8. Une signature invalide sera rejetée.
9. Un émetteur non reconnu pourra être distingué d'un émetteur reconnu.
10. Un credential révoqué pourra être détecté.

Le vérificateur devra notamment réussir un test sans dépendre du backend d'émission KeepYourID.

## 8. Hors périmètre initial

- Facturation et abonnements avancés.
- Multi-blockchain.
- Microservices.
- Automatisation avancée de l'administration.
- Intégrations avec de nombreux fournisseurs d'identité.
- Fonctionnalités avancées de récupération et de délégation.

## 9. Stratégie de développement

Le développement suivra une progression incrémentale :

1. Fondations cryptographiques.
2. DID et résolution.
3. Émission et vérification d'un credential.
4. Gestion des organisations.
5. Wallet.
6. Vérificateur autonome.
7. Révocation.
8. Intégration blockchain complète.
9. Interfaces et intégration finale.

Chaque étape devra être accompagnée de tests automatisés et d'un scénario démontrable.