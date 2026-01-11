# Guide de Vérification des Preuves PoA

## Table des matières / Table of Contents

- [Français](#français)
- [English](#english)

---

# Français

## Guide de Vérification des Preuves PoA

### Vue d'ensemble

Ce guide explique comment vérifier qu'un fichier de preuve privé (`full_client_*.json`) correspond à la version anonymisée publiée sur le dépôt GitHub public. Cette vérification garantit l'intégrité et l'authenticité des preuves sans révéler les données sensibles.

### Concepts Clés

#### Preuve d'Anonymat Atomique

Le système UptimeProof PoA utilise un protocole innovant appelé **"Preuve d'Anonymat Atomique"** qui garantit :

1. **Génération simultanée** : Les versions privée et publique sont créées en même temps en mémoire
2. **Identité absolue** : Le même `proof_id`, `timestamp`, `nonce` et `proof_hash` sont utilisés dans les deux versions
3. **Signature croisée** : Le `proof_hash` et la signature Ed25519 sont calculés sur la version anonymisée, puis injectés dans les deux versions
4. **Anonymisation sécurisée** : Les données sensibles (URLs, noms de monitors, client_id) sont hachées avec `SHA256(valeur + SALT_KEY)` pour protéger la vie privée tout en garantissant l'intégrité

#### Protection de la Vie Privée

Les données sensibles sont anonymisées avec une clé de salage (`SALT_KEY`) :
- `client_id` → `SHA256(client_id + SALT_KEY)`
- `target` / `url` → `SHA256(url + SALT_KEY)`
- `name` (monitors) → `SHA256(name + SALT_KEY)`

Cette approche garantit que :
- Les données sensibles ne sont jamais exposées publiquement
- L'intégrité peut être vérifiée sans connaître les données originales
- La correspondance entre privé et public peut être prouvée via le `proof_hash` identique

### Vérification Pas-à-Pas

#### Étape 1 : Obtenir les fichiers

1. **Fichier privé** : Vous avez reçu un fichier `full_client_*.json` (version privée avec données en clair)
2. **Fichier public** : Téléchargez le fichier correspondant depuis le dépôt GitHub public (même `proof_id`)

#### Étape 2 : Vérifier l'identité absolue

Les deux fichiers doivent avoir les mêmes valeurs pour :
- `proof_id` : Identifiant unique de la preuve
- `timestamp` : Horodatage ISO 8601
- `nonce` : Valeur aléatoire unique
- `proof_hash` : Hash SHA-256 de la version anonymisée

```python
import json

# Charger les deux fichiers
with open("full_client_xxx.json", "r") as f:
    private_data = json.load(f)
with open("client_xxx.json", "r") as f:  # Version publique depuis GitHub
    public_data = json.load(f)

# Vérifier l'identité absolue
assert private_data["proof_id"] == public_data["proof_id"]
assert private_data["timestamp"] == public_data["timestamp"]
assert private_data["nonce"] == public_data["nonce"]
assert private_data["proof_hash"] == public_data["proof_hash"]
print("✓ Identité absolue vérifiée")
```

#### Étape 3 : Vérifier la signature Ed25519

La signature est calculée sur la version anonymisée (publique). Vous pouvez vérifier la signature avec le script standalone ci-dessous.

#### Étape 4 : Vérifier l'anonymisation

Dans le fichier public, vérifiez que :
- `metadata.client_id` est un hash SHA-256 (64 caractères hex)
- `check.target` est un hash SHA-256 (64 caractères hex)
- Les `monitors[].name` sont des hash SHA-256
- Les `monitors[].url` sont des hash SHA-256

### Script Python Standalone (10 lignes)

Voici un script Python minimal que vous pouvez copier-coller pour vérifier une signature Ed25519 :

```python
import json, base64, hashlib
from cryptography.hazmat.primitives.asymmetric import ed25519

proof = json.load(open("proof.json"))
sig_info = proof["signature"]
pub_key = ed25519.Ed25519PublicKey.from_public_bytes(base64.b64decode(sig_info["public_key"]))
data = {k: v for k, v in proof.items() if k != "signature"}
proof_hash = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
pub_key.verify(base64.b64decode(sig_info["signature"]), proof_hash.encode())
print("✓ Signature valide")
```

**Installation de la dépendance** :
```bash
pip install cryptography
```

**Utilisation** :
1. Sauvegardez le script dans un fichier `verify_ed25519.py`
2. Remplacez `"proof.json"` par le chemin vers votre fichier de preuve
3. Exécutez : `python verify_ed25519.py`

### Vérification Complète (Script Complet)

Pour une vérification complète (identité + signature), utilisez ce script :

```python
#!/usr/bin/env python3
"""Vérification complète d'une preuve PoA."""
import json
import base64
import hashlib
import sys
from cryptography.hazmat.primitives.asymmetric import ed25519

def verify_proof(private_file: str, public_file: str):
    """Vérifie qu'un fichier privé correspond à sa version publique."""
    # Charger les fichiers
    with open(private_file, "r") as f:
        private = json.load(f)
    with open(public_file, "r") as f:
        public = json.load(f)
    
    # 1. Vérifier l'identité absolue
    print("1. Vérification de l'identité absolue...")
    assert private["proof_id"] == public["proof_id"], "proof_id différent"
    assert private["timestamp"] == public["timestamp"], "timestamp différent"
    assert private["nonce"] == public["nonce"], "nonce différent"
    assert private["proof_hash"] == public["proof_hash"], "proof_hash différent"
    print("   ✓ Identité absolue vérifiée")
    
    # 2. Vérifier la signature Ed25519
    print("2. Vérification de la signature Ed25519...")
    sig_info = public["signature"]
    if sig_info["status"] != "signed":
        raise ValueError(f"Preuve non signée: {sig_info['status']}")
    
    # Charger la clé publique
    pub_key_bytes = base64.b64decode(sig_info["public_key"])
    pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    
    # Recalculer le proof_hash (sans signature)
    data = {k: v for k, v in public.items() if k != "signature"}
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    proof_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    
    # Vérifier que le hash correspond
    assert proof_hash == sig_info["proof_hash"], "proof_hash ne correspond pas"
    
    # Vérifier la signature
    signature_bytes = base64.b64decode(sig_info["signature"])
    pub_key.verify(signature_bytes, proof_hash.encode("utf-8"))
    print("   ✓ Signature Ed25519 valide")
    
    # 3. Vérifier l'anonymisation
    print("3. Vérification de l'anonymisation...")
    client_id = public.get("metadata", {}).get("client_id", "")
    if client_id and len(client_id) == 64 and all(c in "0123456789abcdef" for c in client_id.lower()):
        print("   ✓ client_id anonymisé")
    else:
        print(f"   ⚠ client_id non anonymisé: {client_id[:32]}...")
    
    print("\n✓ Vérification complète réussie !")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python verify_proof.py <private_file.json> <public_file.json>")
        sys.exit(1)
    
    try:
        verify_proof(sys.argv[1], sys.argv[2])
    except Exception as e:
        print(f"✗ Erreur: {e}")
        sys.exit(1)
```

### Structure des Fichiers

#### Fichier Privé (`full_client_*.json`)

```json
{
  "proof_id": "10767eeb-cbbd-43b8-b9c8-2e1733288a8b",
  "timestamp": "2026-01-11T12:41:57.346560Z",
  "nonce": "cc3190e98346f94f1f5e18fd8fca831ca2010c39226e19c59651fee47906cc45",
  "proof_hash": "3e779cba97553c1092c34096b12f46483dd395a9e24d46bad9ae3c0287b24ea8",
  "metadata": {
    "client_id": "Alpha",  // En clair
    "location": "Paris-VPS"
  },
  "check": {
    "target": "https://example.com",  // En clair
    "success": true
  },
  "signature": {
    "algorithm": "ed25519",
    "status": "signed",
    "proof_hash": "3e779cba97553c1092c34096b12f46483dd395a9e24d46bad9ae3c0287b24ea8",
    "signature": "8XnjMunM5ThzMSNXkmOAoASSKhA/Ec9wB6dWHk5Ypp8CdW3+Ac4+4yArxqTFBCvhcqBAZSHDZmOL2yBQBW3lAg==",
    "public_key": "9PAep13Hnc+pG6HWIBWUOnAiwhc4hbn2ZGAM6BxhwEk="
  }
}
```

#### Fichier Public (`client_*.json`)

```json
{
  "proof_id": "10767eeb-cbbd-43b8-b9c8-2e1733288a8b",  // Identique
  "timestamp": "2026-01-11T12:41:57.346560Z",  // Identique
  "nonce": "cc3190e98346f94f1f5e18fd8fca831ca2010c39226e19c59651fee47906cc45",  // Identique
  "proof_hash": "3e779cba97553c1092c34096b12f46483dd395a9e24d46bad9ae3c0287b24ea8",  // Identique
  "metadata": {
    "client_id": "af67649866da02ac44d6f4ffbbb04453f6b5869d497e6270b84522e79f6bab70",  // Anonymisé
    "location": "Paris-VPS"  // Conservé
  },
  "check": {
    "target": "7ea67688c27161dee1deebd09bee8094d7be7d964f5d959c7f30360265febc12",  // Anonymisé
    "success": true  // Conservé
  },
  "signature": {
    "algorithm": "ed25519",
    "status": "signed",
    "proof_hash": "3e779cba97553c1092c34096b12f46483dd395a9e24d46bad9ae3c0287b24ea8",
    "signature": "8XnjMunM5ThzMSNXkmOAoASSKhA/Ec9wB6dWHk5Ypp8CdW3+Ac4+4yArxqTFBCvhcqBAZSHDZmOL2yBQBW3lAg==",
    "public_key": "9PAep13Hnc+pG6HWIBWUOnAiwhc4hbn2ZGAM6BxhwEk="
  }
}
```

### FAQ

**Q : Pourquoi le `proof_hash` est-il identique dans les deux versions ?**

R : Le `proof_hash` est calculé sur la version anonymisée (publique) uniquement, puis injecté dans les deux versions. Cela garantit que la signature est valide pour la version publique tout en permettant la vérification de correspondance.

**Q : Comment puis-je vérifier que mon fichier privé correspond à la version publique ?**

R : Comparez les champs `proof_id`, `timestamp`, `nonce` et `proof_hash`. Ils doivent être identiques. Ensuite, vérifiez la signature Ed25519 de la version publique.

**Q : Pourquoi les données sensibles sont-elles anonymisées ?**

R : Pour protéger la vie privée des clients tout en permettant la vérification publique de l'intégrité. L'anonymisation avec `SALT_KEY` garantit que seuls les clients avec la clé peuvent reconstituer les données originales.

**Q : Puis-je vérifier la signature sans le fichier privé ?**

R : Oui ! La signature est calculée sur la version publique, donc vous pouvez vérifier n'importe quelle preuve publique directement depuis GitHub.

---

# English

## PoA Proof Verification Guide

### Overview

This guide explains how to verify that a private proof file (`full_client_*.json`) corresponds to the anonymized version published on the public GitHub repository. This verification guarantees the integrity and authenticity of proofs without revealing sensitive data.

### Key Concepts

#### Atomic Anonymity Proof

The UptimeProof PoA system uses an innovative protocol called **"Atomic Anonymity Proof"** that guarantees:

1. **Simultaneous generation** : Private and public versions are created at the same time in memory
2. **Absolute identity** : The same `proof_id`, `timestamp`, `nonce`, and `proof_hash` are used in both versions
3. **Cross signature** : The `proof_hash` and Ed25519 signature are calculated on the anonymized version, then injected into both versions
4. **Secure anonymization** : Sensitive data (URLs, monitor names, client_id) are hashed with `SHA256(value + SALT_KEY)` to protect privacy while guaranteeing integrity

#### Privacy Protection

Sensitive data is anonymized with a salt key (`SALT_KEY`):
- `client_id` → `SHA256(client_id + SALT_KEY)`
- `target` / `url` → `SHA256(url + SALT_KEY)`
- `name` (monitors) → `SHA256(name + SALT_KEY)`

This approach ensures that:
- Sensitive data is never publicly exposed
- Integrity can be verified without knowing original data
- Correspondence between private and public can be proven via identical `proof_hash`

### Step-by-Step Verification

#### Step 1: Get the files

1. **Private file** : You received a `full_client_*.json` file (private version with clear data)
2. **Public file** : Download the corresponding file from the public GitHub repository (same `proof_id`)

#### Step 2: Verify absolute identity

Both files must have the same values for:
- `proof_id` : Unique proof identifier
- `timestamp` : ISO 8601 timestamp
- `nonce` : Unique random value
- `proof_hash` : SHA-256 hash of the anonymized version

```python
import json

# Load both files
with open("full_client_xxx.json", "r") as f:
    private_data = json.load(f)
with open("client_xxx.json", "r") as f:  # Public version from GitHub
    public_data = json.load(f)

# Verify absolute identity
assert private_data["proof_id"] == public_data["proof_id"]
assert private_data["timestamp"] == public_data["timestamp"]
assert private_data["nonce"] == public_data["nonce"]
assert private_data["proof_hash"] == public_data["proof_hash"]
print("✓ Absolute identity verified")
```

#### Step 3: Verify Ed25519 signature

The signature is calculated on the anonymized (public) version. You can verify the signature with the standalone script below.

#### Step 4: Verify anonymization

In the public file, verify that:
- `metadata.client_id` is a SHA-256 hash (64 hex characters)
- `check.target` is a SHA-256 hash (64 hex characters)
- `monitors[].name` are SHA-256 hashes
- `monitors[].url` are SHA-256 hashes

### Standalone Python Script (10 lines)

Here is a minimal Python script you can copy-paste to verify an Ed25519 signature:

```python
import json, base64, hashlib
from cryptography.hazmat.primitives.asymmetric import ed25519

proof = json.load(open("proof.json"))
sig_info = proof["signature"]
pub_key = ed25519.Ed25519PublicKey.from_public_bytes(base64.b64decode(sig_info["public_key"]))
data = {k: v for k, v in proof.items() if k != "signature"}
proof_hash = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
pub_key.verify(base64.b64decode(sig_info["signature"]), proof_hash.encode())
print("✓ Signature valid")
```

**Install dependency** :
```bash
pip install cryptography
```

**Usage** :
1. Save the script in a file `verify_ed25519.py`
2. Replace `"proof.json"` with the path to your proof file
3. Run : `python verify_ed25519.py`

### Complete Verification (Full Script)

For complete verification (identity + signature), use this script:

```python
#!/usr/bin/env python3
"""Complete PoA proof verification."""
import json
import base64
import hashlib
import sys
from cryptography.hazmat.primitives.asymmetric import ed25519

def verify_proof(private_file: str, public_file: str):
    """Verifies that a private file corresponds to its public version."""
    # Load files
    with open(private_file, "r") as f:
        private = json.load(f)
    with open(public_file, "r") as f:
        public = json.load(f)
    
    # 1. Verify absolute identity
    print("1. Verifying absolute identity...")
    assert private["proof_id"] == public["proof_id"], "proof_id differs"
    assert private["timestamp"] == public["timestamp"], "timestamp differs"
    assert private["nonce"] == public["nonce"], "nonce differs"
    assert private["proof_hash"] == public["proof_hash"], "proof_hash differs"
    print("   ✓ Absolute identity verified")
    
    # 2. Verify Ed25519 signature
    print("2. Verifying Ed25519 signature...")
    sig_info = public["signature"]
    if sig_info["status"] != "signed":
        raise ValueError(f"Proof not signed: {sig_info['status']}")
    
    # Load public key
    pub_key_bytes = base64.b64decode(sig_info["public_key"])
    pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    
    # Recalculate proof_hash (without signature)
    data = {k: v for k, v in public.items() if k != "signature"}
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    proof_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    
    # Verify hash matches
    assert proof_hash == sig_info["proof_hash"], "proof_hash does not match"
    
    # Verify signature
    signature_bytes = base64.b64decode(sig_info["signature"])
    pub_key.verify(signature_bytes, proof_hash.encode("utf-8"))
    print("   ✓ Ed25519 signature valid")
    
    # 3. Verify anonymization
    print("3. Verifying anonymization...")
    client_id = public.get("metadata", {}).get("client_id", "")
    if client_id and len(client_id) == 64 and all(c in "0123456789abcdef" for c in client_id.lower()):
        print("   ✓ client_id anonymized")
    else:
        print(f"   ⚠ client_id not anonymized: {client_id[:32]}...")
    
    print("\n✓ Complete verification successful !")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python verify_proof.py <private_file.json> <public_file.json>")
        sys.exit(1)
    
    try:
        verify_proof(sys.argv[1], sys.argv[2])
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
```

### File Structure

#### Private File (`full_client_*.json`)

```json
{
  "proof_id": "10767eeb-cbbd-43b8-b9c8-2e1733288a8b",
  "timestamp": "2026-01-11T12:41:57.346560Z",
  "nonce": "cc3190e98346f94f1f5e18fd8fca831ca2010c39226e19c59651fee47906cc45",
  "proof_hash": "3e779cba97553c1092c34096b12f46483dd395a9e24d46bad9ae3c0287b24ea8",
  "metadata": {
    "client_id": "Alpha",  // Clear text
    "location": "Paris-VPS"
  },
  "check": {
    "target": "https://example.com",  // Clear text
    "success": true
  },
  "signature": {
    "algorithm": "ed25519",
    "status": "signed",
    "proof_hash": "3e779cba97553c1092c34096b12f46483dd395a9e24d46bad9ae3c0287b24ea8",
    "signature": "8XnjMunM5ThzMSNXkmOAoASSKhA/Ec9wB6dWHk5Ypp8CdW3+Ac4+4yArxqTFBCvhcqBAZSHDZmOL2yBQBW3lAg==",
    "public_key": "9PAep13Hnc+pG6HWIBWUOnAiwhc4hbn2ZGAM6BxhwEk="
  }
}
```

#### Public File (`client_*.json`)

```json
{
  "proof_id": "10767eeb-cbbd-43b8-b9c8-2e1733288a8b",  // Identical
  "timestamp": "2026-01-11T12:41:57.346560Z",  // Identical
  "nonce": "cc3190e98346f94f1f5e18fd8fca831ca2010c39226e19c59651fee47906cc45",  // Identical
  "proof_hash": "3e779cba97553c1092c34096b12f46483dd395a9e24d46bad9ae3c0287b24ea8",  // Identical
  "metadata": {
    "client_id": "af67649866da02ac44d6f4ffbbb04453f6b5869d497e6270b84522e79f6bab70",  // Anonymized
    "location": "Paris-VPS"  // Preserved
  },
  "check": {
    "target": "7ea67688c27161dee1deebd09bee8094d7be7d964f5d959c7f30360265febc12",  // Anonymized
    "success": true  // Preserved
  },
  "signature": {
    "algorithm": "ed25519",
    "status": "signed",
    "proof_hash": "3e779cba97553c1092c34096b12f46483dd395a9e24d46bad9ae3c0287b24ea8",
    "signature": "8XnjMunM5ThzMSNXkmOAoASSKhA/Ec9wB6dWHk5Ypp8CdW3+Ac4+4yArxqTFBCvhcqBAZSHDZmOL2yBQBW3lAg==",
    "public_key": "9PAep13Hnc+pG6HWIBWUOnAiwhc4hbn2ZGAM6BxhwEk="
  }
}
```

### FAQ

**Q: Why is `proof_hash` identical in both versions?**

A: The `proof_hash` is calculated on the anonymized (public) version only, then injected into both versions. This ensures the signature is valid for the public version while allowing correspondence verification.

**Q: How can I verify that my private file corresponds to the public version?**

A: Compare the `proof_id`, `timestamp`, `nonce`, and `proof_hash` fields. They must be identical. Then verify the Ed25519 signature of the public version.

**Q: Why are sensitive data anonymized?**

A: To protect client privacy while allowing public verification of integrity. Anonymization with `SALT_KEY` ensures only clients with the key can reconstruct original data.

**Q: Can I verify the signature without the private file?**

A: Yes! The signature is calculated on the public version, so you can verify any public proof directly from GitHub.
