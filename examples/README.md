# Exemples de Preuves PoA

## Format Synchronisé v2.4

Ces exemples illustrent le format synchronisé des preuves PoA avec anonymisation atomique.

### Fichiers

- **`example_private.json`** : Version privée avec données en clair
- **`example_public.json`** : Version publique anonymisée (publiée sur GitHub)

### Correspondance

Les deux fichiers partagent une **identité absolue** :

- ✅ `proof_id` : Identique (`10767eeb-cbbd-43b8-b9c8-2e1733288a8b`)
- ✅ `timestamp` : Identique (`2026-01-11T12:00:00.000000Z`)
- ✅ `nonce` : Identique
- ✅ `proof_hash` : Identique (`3e779cba97553c1092c34096b12f46483dd395a9e24d46bad9ae3c0287b24ea8`)
- ✅ `signature` : Identique

### Anonymisation

Dans la version publique, les données sensibles sont anonymisées :

- `metadata.client_id` : `"Alpha"` → `"af67649866da02ac44d6f4ffbbb04453f6b5869d497e6270b84522e79f6bab70"` (SHA256)
- `monitors[].name` : `"Google-Check"` → `"158cebfb2b05af95063afcdd2ed313e7912302531f7e94eae081477b26f4a03c"` (SHA256)
- `monitors[].url` : `"https://www.google.com/"` → `"7ea67688c27161dee1deebd09bee8094d7be7d964f5d959c7f30360265febc12"` (SHA256)
- `kuma_url` : `"http://uptime-kuma:3001"` → `"a5d22ad20f7313043de93f4b0ad99af964a5009ab2c1b1446805cece4214ca93"` (SHA256)

### Vérification

Pour vérifier que les deux fichiers correspondent :

```python
import json

with open("example_private.json", "r") as f:
    private = json.load(f)
with open("example_public.json", "r") as f:
    public = json.load(f)

# Vérifier l'identité absolue
assert private["proof_id"] == public["proof_id"]
assert private["timestamp"] == public["timestamp"]
assert private["nonce"] == public["nonce"]
assert private["proof_hash"] == public["proof_hash"]
print("✓ Correspondance vérifiée")
```

Pour vérifier la signature Ed25519, voir `VERIFY.md`.
