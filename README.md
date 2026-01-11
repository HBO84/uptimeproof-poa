# 🛡️ UptimeProof - Public Transparency Portal

**Portail public de transparence pour la vérification des preuves de disponibilité**

[![Version](https://img.shields.io/badge/version-2.4.0-blue.svg)](https://github.com/HBO84/uptimeproof)
[![Protocol](https://img.shields.io/badge/protocol-Atomic%20Anonymity-green.svg)](PROTOCOL.md)

---

## 🚀 Vérification des Preuves (Client)

Vous avez reçu un fichier de preuve privé (`full_client_*.json`) et vous voulez vérifier qu'il correspond à la version anonymisée publiée ici ?

👉 **[Consultez le guide complet : VERIFY.md](VERIFY.md)**

Le guide inclut :
- ✅ Vérification pas-à-pas en 4 étapes
- ✅ Script Python standalone de 10 lignes pour vérifier Ed25519
- ✅ Script complet de vérification (identité + signature)
- ✅ FAQ et exemples pratiques

### Vérification Rapide (3 étapes)

1. **Téléchargez votre fichier public** depuis ce dépôt (même `proof_id`)
2. **Comparez l'identité absolue** :
   ```python
   assert private["proof_id"] == public["proof_id"]
   assert private["proof_hash"] == public["proof_hash"]
   ```
3. **Vérifiez la signature Ed25519** avec le script Python (voir [VERIFY.md](VERIFY.md))

---

## 📜 Protocole PoA v2.4

Le système UptimeProof utilise un protocole innovant appelé **"Preuve d'Anonymat Atomique"** qui garantit l'intégrité, l'authenticité et la protection de la vie privée.

👉 **[Documentation complète : PROTOCOL.md](PROTOCOL.md)**

### Caractéristiques du Protocole

- **🔐 Anonymisation Atomique** : Génération simultanée des versions privée et publique
- **🔒 Signature Ed25519** : Cryptographie moderne pour l'authenticité
- **🛡️ Protection de la Vie Privée** : Données sensibles hachées avec SALT_KEY
- **🔗 Chaînage Cryptographique** : Liens entre preuves successives
- **✅ Identité Absolue** : Même `proof_id` entre privé et public

### Sécurité

Ce dépôt contient les preuves d'intégrité anonymisées. **Aucun nom de client ou URL n'est exposé** grâce au hachage salé (Salted Hashing). Les données sensibles sont irréversiblement anonymisées avec `SHA256(valeur + SALT_KEY)`.

---

## 📁 Structure

```
UptimeProof-poa/
├── README.md          # Ce fichier (portail client)
├── VERIFY.md          # Guide de vérification complet
├── PROTOCOL.md        # Documentation du protocole v2.4
├── examples/          # Exemples synchronisés privé/public
└── proofs/            # Preuves publiques anonymisées
```

---

## 🔍 Exemples

Consultez le dossier **[examples/](examples/)** pour voir :
- `example_private.json` : Version privée (en clair)
- `example_public.json` : Version publique (anonymisée)
- Correspondance 1:1 démontrée

---

## 📚 Documentation

- **[VERIFY.md](VERIFY.md)** : Guide de vérification pas-à-pas (FR/EN)
- **[PROTOCOL.md](PROTOCOL.md)** : Documentation technique du protocole
- **[examples/README.md](examples/README.md)** : Documentation des exemples

---

## 🔗 Liens

- **Repo Technique** : [uptimeproof](https://github.com/HBO84/uptimeproof) (privé)
- **Version** : 2.4.0
- **Protocole** : Atomic Anonymity Proof

---

**UptimeProof v2.4** - Preuve de disponibilité vérifiable et publique

*Toutes les preuves sont signées avec Ed25519 et anonymisées pour protéger la vie privée des clients.*
