# UptimeProof - Preuves Publiques

**Portail public pour la vérification des preuves de disponibilité**

[![Version](https://img.shields.io/badge/version-2.4.0-blue.svg)](https://github.com/HBO84/uptimeproof)
[![Protocol](https://img.shields.io/badge/protocol-Atomic%20Anonymity-green.svg)](PROTOCOL.md)

## 🎯 Comment vérifier ma preuve ?

Vous avez reçu un fichier `full_client_*.json` (version privée) et vous voulez vérifier qu'il correspond à la version anonymisée publiée ici ?

👉 **[Consultez le guide complet : VERIFY.md](VERIFY.md)**

### Vérification rapide (3 étapes)

1. **Téléchargez votre fichier public** depuis ce dépôt (même `proof_id`)
2. **Comparez l'identité absolue** :
   ```python
   assert private["proof_id"] == public["proof_id"]
   assert private["proof_hash"] == public["proof_hash"]
   ```
3. **Vérifiez la signature Ed25519** avec le script Python de 10 lignes (voir [VERIFY.md](VERIFY.md))

### Script Python Standalone (10 lignes)

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

**Installation** : `pip install cryptography`

## 📚 Documentation

### Guides

- **[VERIFY.md](VERIFY.md)** : Guide complet de vérification (FR/EN)
  - Vérification pas-à-pas
  - Script Python standalone
  - FAQ et exemples

- **[PROTOCOL.md](PROTOCOL.md)** : Documentation du protocole "Preuve d'Anonymat Atomique"
  - Architecture du protocole
  - Protection de la vie privée
  - Anonymisation sécurisée

### Exemples

- **[examples/](examples/)** : Exemples de fichiers synchronisés
  - `example_private.json` : Version privée (en clair)
  - `example_public.json` : Version publique (anonymisée)
  - Correspondance 1:1 démontrée

## 🔒 Protocole : Preuve d'Anonymat Atomique

Le système UptimeProof utilise un protocole innovant qui garantit :

✅ **Intégrité** : Signature Ed25519 cryptographique  
✅ **Authenticité** : Preuve de l'origine des données  
✅ **Vie privée** : Données sensibles anonymisées (SHA256 + SALT_KEY)  
✅ **Traçabilité** : Identité absolue entre privé et public  

### Caractéristiques

- **Génération atomique** : Versions privée et publique créées simultanément
- **Identité absolue** : Même `proof_id`, `timestamp`, `nonce`, `proof_hash`
- **Signature croisée** : Calculée sur la version anonymisée, injectée dans les deux
- **Anonymisation irréversible** : SHA256(valeur + SALT_KEY)

## 📁 Structure des Preuves

### Fichier Privé (`full_client_*.json`)

Contient toutes les données en clair :
- URLs des services
- Noms des monitors
- Identifiants clients
- Métadonnées complètes

### Fichier Public (`client_*.json`)

Contient les données anonymisées :
- `client_id` → Hash SHA-256
- `target` / `url` → Hash SHA-256
- `name` (monitors) → Hash SHA-256
- Signature Ed25519 complète

**Les deux fichiers partagent** :
- `proof_id` (identique)
- `timestamp` (identique)
- `nonce` (identique)
- `proof_hash` (identique)
- `signature` (identique)

## 🔍 Vérification de Correspondance

Pour vérifier que votre fichier privé correspond à la version publique :

```python
import json

with open("full_client_xxx.json", "r") as f:
    private = json.load(f)
with open("client_xxx.json", "r") as f:  # Depuis ce dépôt
    public = json.load(f)

# Vérifier l'identité absolue
assert private["proof_id"] == public["proof_id"]
assert private["timestamp"] == public["timestamp"]
assert private["nonce"] == public["nonce"]
assert private["proof_hash"] == public["proof_hash"]
assert private["signature"] == public["signature"]

print("✓ Correspondance vérifiée")
```

## 📊 Preuves Disponibles

Les preuves publiques sont organisées par date et client. Chaque preuve est :
- ✅ Signée avec Ed25519
- ✅ Anonymisée (données sensibles hashées)
- ✅ Chaînée avec la preuve précédente
- ✅ Vérifiable publiquement

## 🛠️ Outils

### Vérification en ligne

Utilisez le script Python fourni dans [VERIFY.md](VERIFY.md) pour vérifier n'importe quelle preuve.

### API de vérification

```bash
curl https://api.uptimeproof.io/poa/v1/verify?proof_id=...
```

## 🔗 Liens

- **Repo Technique** : [uptimeproof](https://github.com/HBO84/uptimeproof) (privé)
- **Guide de Vérification** : [VERIFY.md](VERIFY.md)
- **Documentation du Protocole** : [PROTOCOL.md](PROTOCOL.md)
- **Exemples** : [examples/](examples/)

## 📝 FAQ

**Q : Pourquoi mes données sont-elles anonymisées ?**  
R : Pour protéger votre vie privée tout en permettant la vérification publique de l'intégrité.

**Q : Puis-je vérifier la signature sans le fichier privé ?**  
R : Oui ! La signature est calculée sur la version publique, donc vous pouvez vérifier n'importe quelle preuve directement.

**Q : Comment puis-je prouver que mon fichier privé correspond à la version publique ?**  
R : Comparez les champs `proof_id`, `timestamp`, `nonce`, `proof_hash` et `signature`. Ils doivent être identiques.

**Q : Les données anonymisées peuvent-elles être reconstituées ?**  
R : Non, l'anonymisation utilise SHA256 + SALT_KEY, ce qui est irréversible sans la clé secrète.

---

**UptimeProof v2.4** - Preuve de disponibilité vérifiable et publique
