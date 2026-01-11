# Protocole PoA - Preuve d'Anonymat Atomique

## Table des matières / Table of Contents

- [Français](#français)
- [English](#english)

---

# Français

## Protocole PoA - Preuve d'Anonymat Atomique

### Introduction

Le protocole **"Preuve d'Anonymat Atomique"** (Atomic Anonymity Proof) est une innovation d'UptimeProof PoA qui garantit l'intégrité et l'authenticité des preuves de disponibilité tout en protégeant la vie privée des clients. Ce protocole permet de publier des preuves vérifiables publiquement sans révéler les données sensibles.

### Concept Fondamental

#### Le Problème

Dans un système de preuve de disponibilité, nous devons :
1. **Prouver l'intégrité** : Garantir que les données n'ont pas été modifiées
2. **Prouver l'authenticité** : Garantir que les données proviennent d'une source fiable
3. **Protéger la vie privée** : Ne pas exposer les URLs, noms de services, ou identifiants clients

#### La Solution : Preuve d'Anonymat Atomique

Le protocole résout ce problème en créant **deux versions synchronisées** d'une même preuve :

1. **Version Privée** : Contient toutes les données en clair (pour le client)
2. **Version Publique** : Contient les données anonymisées (pour publication GitHub)

Les deux versions partagent une **identité absolue** via des champs communs qui permettent de prouver leur correspondance sans révéler les données sensibles.

### Architecture du Protocole

#### Étape 1 : Génération Atomique

Les deux versions sont générées **simultanément en mémoire** :

```
┌─────────────────────────────────────────┐
│  Données brutes (Uptime Kuma)           │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ Version      │  │ Version      │
│ Privée       │  │ Publique     │
│ (Clair)      │  │ (Anonymisée) │
└──────────────┘  └──────────────┘
```

**Caractéristiques** :
- Génération synchrone (zéro latence)
- Même `proof_id`, `timestamp`, `nonce` générés une seule fois
- Anonymisation appliquée uniquement à la version publique

#### Étape 2 : Anonymisation Sécurisée

Les données sensibles sont anonymisées avec une clé de salage (`SALT_KEY`) :

**Algorithme d'anonymisation** :
```
hash = SHA256(valeur + SALT_KEY)
```

**Champs anonymisés** :
- `metadata.client_id` → `SHA256(client_id + SALT_KEY)`
- `check.target` → `SHA256(url + SALT_KEY)`
- `monitors[].name` → `SHA256(name + SALT_KEY)`
- `monitors[].url` → `SHA256(url + SALT_KEY)`
- `kuma_url` → `SHA256(kuma_url + SALT_KEY)`

**Champs conservés en clair** :
- `timestamp` : Horodatage (non sensible)
- `nonce` : Valeur aléatoire (non sensible)
- `success` : Statut de disponibilité (non sensible)
- `status_code` : Code HTTP (non sensible)
- `location` : Localisation géographique (optionnel, non sensible)
- `response_time_ms` : Latence (non sensible)

#### Étape 3 : Calcul du Proof Hash

Le `proof_hash` est calculé **uniquement sur la version anonymisée** :

```python
# Version anonymisée (sans signature)
data = {k: v for k, v in public_data.items() if k != "signature"}
json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
proof_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
```

**Pourquoi uniquement la version anonymisée ?**
- La version publique est celle qui sera publiée sur GitHub
- La signature doit être vérifiable publiquement
- L'intégrité est garantie sur les données publiques

#### Étape 4 : Signature Ed25519

La signature cryptographique est calculée sur le `proof_hash` :

```python
# Signer le hash (pas le JSON complet)
signature_bytes = private_key.sign(proof_hash.encode("utf-8"))
signature_b64 = base64.b64encode(signature_bytes).decode("ascii")
```

**Caractéristiques** :
- Algorithme : Ed25519 (courbe elliptique)
- Signature du hash (64 bytes → 88 caractères base64)
- Clé publique incluse dans la preuve pour vérification

#### Étape 5 : Injection Croisée

Le `proof_hash` et la `signature` sont injectés dans **les deux versions** :

```
┌─────────────────────────────────────────┐
│  proof_hash (calculé sur version pub)  │
│  signature (Ed25519 du proof_hash)     │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ Version      │  │ Version      │
│ Privée       │  │ Publique     │
│ + proof_hash │  │ + proof_hash │
│ + signature  │  │ + signature  │
└──────────────┘  └──────────────┘
```

**Résultat** : Les deux versions ont le même `proof_hash` et la même `signature`, permettant la vérification de correspondance.

### Identité Absolue

Les champs suivants sont **identiques** dans les deux versions :

1. **`proof_id`** : UUID v4 unique généré une seule fois
2. **`timestamp`** : Horodatage ISO 8601 UTC avec microsecondes
3. **`nonce`** : Valeur aléatoire de 32 bytes (64 caractères hex)
4. **`proof_hash`** : Hash SHA-256 de la version anonymisée
5. **`signature`** : Signature Ed25519 complète

Cette identité absolue permet de :
- Prouver que les deux versions correspondent
- Vérifier l'intégrité sans révéler les données sensibles
- Garantir la traçabilité entre privé et public

### Vérification de Correspondance

Un client peut vérifier que son fichier privé correspond à la version publique en comparant :

```python
assert private["proof_id"] == public["proof_id"]
assert private["timestamp"] == public["timestamp"]
assert private["nonce"] == public["nonce"]
assert private["proof_hash"] == public["proof_hash"]
assert private["signature"] == public["signature"]
```

Si tous ces champs sont identiques, les deux versions correspondent.

### Vérification de Signature

La signature peut être vérifiée indépendamment sur la version publique :

```python
# 1. Charger la clé publique
pub_key = ed25519.Ed25519PublicKey.from_public_bytes(
    base64.b64decode(public["signature"]["public_key"])
)

# 2. Recalculer le proof_hash
data = {k: v for k, v in public.items() if k != "signature"}
json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
proof_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

# 3. Vérifier la signature
signature_bytes = base64.b64decode(public["signature"]["signature"])
pub_key.verify(signature_bytes, proof_hash.encode("utf-8"))
```

### Protection de la Vie Privée

#### Anonymisation Irréversible

L'anonymisation avec `SALT_KEY` garantit que :
- Les données sensibles ne peuvent pas être reconstituées sans la clé
- Chaque client a sa propre clé (isolation)
- Les hashs sont uniques et non réversibles

#### Isolation des Clients

Chaque client a sa propre `SALT_KEY`, garantissant :
- L'isolation complète entre clients
- L'impossibilité de corréler les données entre clients
- La protection contre les attaques par analyse

### Avantages du Protocole

1. **Transparence** : Les preuves publiques sont vérifiables par tous
2. **Intégrité** : Signature cryptographique garantit l'authenticité
3. **Vie privée** : Données sensibles protégées par anonymisation
4. **Traçabilité** : Identité absolue permet la correspondance privé/public
5. **Performance** : Génération atomique sans latence
6. **Robustesse** : Vérifications automatiques à chaque étape

### Limitations et Considérations

1. **SALT_KEY requise** : L'anonymisation nécessite une clé secrète
2. **Non-réversibilité** : Les données anonymisées ne peuvent pas être reconstituées sans la clé
3. **Dépendance cryptographique** : Basé sur SHA-256 et Ed25519 (considérés sécurisés)

### Conclusion

Le protocole "Preuve d'Anonymat Atomique" offre une solution élégante au problème de la preuve de disponibilité avec protection de la vie privée. Il garantit l'intégrité, l'authenticité et la traçabilité tout en protégeant les données sensibles des clients.

---

# English

## PoA Protocol - Atomic Anonymity Proof

### Introduction

The **"Atomic Anonymity Proof"** protocol is an UptimeProof PoA innovation that guarantees the integrity and authenticity of availability proofs while protecting client privacy. This protocol allows publishing verifiable proofs publicly without revealing sensitive data.

### Fundamental Concept

#### The Problem

In an availability proof system, we must:
1. **Prove integrity** : Guarantee that data has not been modified
2. **Prove authenticity** : Guarantee that data comes from a trusted source
3. **Protect privacy** : Do not expose URLs, service names, or client identifiers

#### The Solution: Atomic Anonymity Proof

The protocol solves this problem by creating **two synchronized versions** of the same proof:

1. **Private Version** : Contains all data in clear text (for the client)
2. **Public Version** : Contains anonymized data (for GitHub publication)

Both versions share an **absolute identity** via common fields that allow proving their correspondence without revealing sensitive data.

### Protocol Architecture

#### Step 1: Atomic Generation

Both versions are generated **simultaneously in memory** :

```
┌─────────────────────────────────────────┐
│  Raw data (Uptime Kuma)                │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ Private      │  │ Public       │
│ Version      │  │ Version      │
│ (Clear)      │  │ (Anonymized) │
└──────────────┘  └──────────────┘
```

**Features** :
- Synchronous generation (zero latency)
- Same `proof_id`, `timestamp`, `nonce` generated once
- Anonymization applied only to public version

#### Step 2: Secure Anonymization

Sensitive data is anonymized with a salt key (`SALT_KEY`) :

**Anonymization algorithm** :
```
hash = SHA256(value + SALT_KEY)
```

**Anonymized fields** :
- `metadata.client_id` → `SHA256(client_id + SALT_KEY)`
- `check.target` → `SHA256(url + SALT_KEY)`
- `monitors[].name` → `SHA256(name + SALT_KEY)`
- `monitors[].url` → `SHA256(url + SALT_KEY)`
- `kuma_url` → `SHA256(kuma_url + SALT_KEY)`

**Preserved clear fields** :
- `timestamp` : Timestamp (non-sensitive)
- `nonce` : Random value (non-sensitive)
- `success` : Availability status (non-sensitive)
- `status_code` : HTTP code (non-sensitive)
- `location` : Geographic location (optional, non-sensitive)
- `response_time_ms` : Latency (non-sensitive)

#### Step 3: Proof Hash Calculation

The `proof_hash` is calculated **only on the anonymized version** :

```python
# Anonymized version (without signature)
data = {k: v for k, v in public_data.items() if k != "signature"}
json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
proof_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
```

**Why only the anonymized version?**
- The public version is the one that will be published on GitHub
- The signature must be publicly verifiable
- Integrity is guaranteed on public data

#### Step 4: Ed25519 Signature

The cryptographic signature is calculated on the `proof_hash` :

```python
# Sign the hash (not the complete JSON)
signature_bytes = private_key.sign(proof_hash.encode("utf-8"))
signature_b64 = base64.b64encode(signature_bytes).decode("ascii")
```

**Features** :
- Algorithm : Ed25519 (elliptic curve)
- Hash signature (64 bytes → 88 base64 characters)
- Public key included in proof for verification

#### Step 5: Cross Injection

The `proof_hash` and `signature` are injected into **both versions** :

```
┌─────────────────────────────────────────┐
│  proof_hash (calculated on public ver)  │
│  signature (Ed25519 of proof_hash)    │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ Private      │  │ Public       │
│ Version      │  │ Version      │
│ + proof_hash │  │ + proof_hash │
│ + signature  │  │ + signature  │
└──────────────┘  └──────────────┘
```

**Result** : Both versions have the same `proof_hash` and `signature`, allowing correspondence verification.

### Absolute Identity

The following fields are **identical** in both versions :

1. **`proof_id`** : Unique UUID v4 generated once
2. **`timestamp`** : ISO 8601 UTC timestamp with microseconds
3. **`nonce`** : Random 32-byte value (64 hex characters)
4. **`proof_hash`** : SHA-256 hash of anonymized version
5. **`signature`** : Complete Ed25519 signature

This absolute identity allows :
- Proving that both versions correspond
- Verifying integrity without revealing sensitive data
- Guaranteeing traceability between private and public

### Correspondence Verification

A client can verify that their private file corresponds to the public version by comparing :

```python
assert private["proof_id"] == public["proof_id"]
assert private["timestamp"] == public["timestamp"]
assert private["nonce"] == public["nonce"]
assert private["proof_hash"] == public["proof_hash"]
assert private["signature"] == public["signature"]
```

If all these fields are identical, both versions correspond.

### Signature Verification

The signature can be verified independently on the public version :

```python
# 1. Load public key
pub_key = ed25519.Ed25519PublicKey.from_public_bytes(
    base64.b64decode(public["signature"]["public_key"])
)

# 2. Recalculate proof_hash
data = {k: v for k, v in public.items() if k != "signature"}
json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
proof_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

# 3. Verify signature
signature_bytes = base64.b64decode(public["signature"]["signature"])
pub_key.verify(signature_bytes, proof_hash.encode("utf-8"))
```

### Privacy Protection

#### Irreversible Anonymization

Anonymization with `SALT_KEY` guarantees that :
- Sensitive data cannot be reconstructed without the key
- Each client has its own key (isolation)
- Hashes are unique and non-reversible

#### Client Isolation

Each client has its own `SALT_KEY`, guaranteeing :
- Complete isolation between clients
- Impossibility to correlate data between clients
- Protection against analysis attacks

### Protocol Advantages

1. **Transparency** : Public proofs are verifiable by all
2. **Integrity** : Cryptographic signature guarantees authenticity
3. **Privacy** : Sensitive data protected by anonymization
4. **Traceability** : Absolute identity allows private/public correspondence
5. **Performance** : Atomic generation without latency
6. **Robustness** : Automatic verifications at each step

### Limitations and Considerations

1. **SALT_KEY required** : Anonymization requires a secret key
2. **Non-reversibility** : Anonymized data cannot be reconstructed without the key
3. **Cryptographic dependency** : Based on SHA-256 and Ed25519 (considered secure)

### Conclusion

The "Atomic Anonymity Proof" protocol offers an elegant solution to the availability proof problem with privacy protection. It guarantees integrity, authenticity, and traceability while protecting client sensitive data.
