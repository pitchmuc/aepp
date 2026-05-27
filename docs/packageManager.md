# PackageManager for AEP Sandbox Tooling

This module is a custom module built by Adobe Consulting team in order to improve efficiency of Sandbox Tooling package creation, management, and import workflows.\
The Package Manager is built on top of the existing [AEP Sandbox Tooling API](https://experienceleague.adobe.com/en/docs/experience-platform/sandbox/sandbox-tooling-api/packages) and the [Sandboxes class](./sandboxes.md).

Sandbox Tooling allows you to select different artifacts (also known as objects) and export them into a package. A package can consist of a single artifact or multiple artifacts (such as datasets or schemas). Any artifacts included in a package must be from the same sandbox.

## Menu
- [Instantiation](#instantiation)
- [Package Manager attributes](#package-manager-attributes)
- [Package Manager methods](#package-manager-methods)
- [Artifact types reference](#artifact-types-reference)
- [Workflow examples](#workflow-examples)

## Instantiation

The `PackageManager` is a class that can be instantiated with different parameters:

* package : OPTIONAL : A dictionary representing an existing package definition. If you retrieve a package via the `Sandboxes` class (e.g. `getPackage`), you can pass it here to load an existing package.
* config : REQUIRED : A [`ConnectObject` instance](./getting-started.md#the-connectinstance-parameter). Ensures the correct sandbox and organisation context.
* name : OPTIONAL : Name of the package to create. **Required** when creating a new package (i.e. when `package` is not provided).
* description : OPTIONAL : A description for the package. Defaults to `"power by aepp"`.
* packageType : OPTIONAL : Either `"PARTIAL"` (default) to include specific artifacts, or `"FULL"` to copy the entire source sandbox.
* artifacts : OPTIONAL : A list of artifact dictionaries to include in the package when `packageType` is `"PARTIAL"`.
  ```python
  [
      {"id": "27115daa-c92b-4f17-a077-d65ffeb0c525", "title": "My Segment", "type": "PROFILE_SEGMENT"},
      {"id": "d8d8ed6d-696a-40bd-b4fe-ca053ec94e29", "title": "My Journey",  "type": "JOURNEY"}
  ]
  ```
* expiry : OPTIONAL : The expiry of the package. Either an integer representing the number of days from today (default `90`) or an ISO 8601 string such as `"2023-05-20T20:05:10Z"`.


### 1 Loading an existing package

```python
import aepp
from aepp import sandboxes

mySandbox = aepp.importConfigFile('myconfig.json', sandbox='mysandbox', connectInstance=True)
sandboxInstance = sandboxes.Sandboxes(config=mySandbox)

# Retrieve the raw package dictionary
existingPackage = sandboxInstance.getPackage('209f886b00444eac9bb5836fe32e7681')

# Wrap it in a PackageManager for convenient manipulation
pkgManager = sandboxes.PackageManager(package=existingPackage, config=mySandbox)
```

### 2 Creating a new PARTIAL package

```python
import aepp
from aepp import sandboxes

mySandbox = aepp.importConfigFile('myconfig.json', sandbox='mysandbox', connectInstance=True)

pkgManager = sandboxes.PackageManager(
    config=mySandbox,
    name='My Package',
    description='Contains key segments and schemas',
    packageType='PARTIAL',
    expiry=60  # expires in 60 days
)

# Add artifacts before creating
pkgManager.addArtifact(
    artifact='27115daa-c92b-4f17-a077-d65ffeb0c525',
    artifactType='PROFILE_SEGMENT',
    title='My Segment'
)

# Push the package to AEP
pkgManager.createPackage()
```

### 3 Creating a FULL sandbox copy package

```python
import aepp
from aepp import sandboxes

mySandbox = aepp.importConfigFile('myconfig.json', sandbox='mysandbox', connectInstance=True)

pkgManager = sandboxes.PackageManager(
    config=mySandbox,
    name='Full Sandbox Copy',
    packageType='FULL',
    expiry=30
)

pkgManager.createPackage()
```

## Package Manager attributes

Once you have instantiated the `PackageManager` you can access the following attributes directly on the instance:

* `ARTIFACT_TYPES` : A list of all supported artifact type strings (see [Artifact types reference](#artifact-types-reference))
* `sandbox` : Name of the source sandbox
* `status` : Current package status — `"NEW"` for a locally-defined package not yet pushed to AEP, or the API-returned status (e.g. `"DRAFT"`, `"PUBLISHED"`) for an existing package
* `id` : The package ID returned by the API after creation (`None` for new packages)
* `name` : The package name
* `description` : The package description
* `packageType` : Either `"PARTIAL"` or `"FULL"`
* `sourceSandbox` : The source sandbox name (populated when loading an existing package)
* `artifacts` : The current list of artifact dictionaries included in the package
* `expiry` : The package expiration date-time string in ISO 8601 UTC format
* `package` : The full package dictionary as returned by the API (or the locally built definition for new packages)
* `tooling_api` : The underlying `Sandboxes` instance used for API calls (available for new packages)

## Package Manager methods

There are several methods available once you have instantiated a `PackageManager` class.\
Note that setter methods (`setName`, `setDescription`, `setExpiry`, `setFullPackage`) only update the local state.\
Changes are persisted to AEP only when `createPackage`, `updatePackageInfo`, `addArtifact`, or `deleteArtifact` are called.

---

### setName

Set or override the name of the package locally.\
Arguments:
* name : REQUIRED : The new name for the package

```python
pkgManager.setName('Updated Package Name')
```

---

### setDescription

Set or override the description of the package locally.\
Argument:
* description : REQUIRED : The new description for the package

```python
pkgManager.setDescription('A revised description for the package')
```

---

### setFullPackage

Toggle the package type between `FULL` and `PARTIAL`.\
Argument:
* fullPackage : OPTIONAL : Boolean. If `True`, sets `packageType` to `"FULL"`. If `False` (default), sets it to `"PARTIAL"`.

```python
pkgManager.setFullPackage(True)   # sets packageType to "FULL"
pkgManager.setFullPackage(False)  # sets packageType to "PARTIAL"
```

---

### setExpiry

Update the expiration of the package.\
Argument:
* expiry : REQUIRED : Either an integer (number of days from today) or an ISO 8601 string (e.g. `"2024-01-01T00:00:00Z"`)

```python
pkgManager.setExpiry(120)                      # 120 days from now
pkgManager.setExpiry('2024-06-01T00:00:00Z')   # explicit date
```

---

### addArtifact

Add an artifact to the package.\
* If the package is **new** (status `"NEW"`), the artifact is added to the local `artifacts` list. Call `createPackage` afterwards to persist.
* If the package **already exists** in AEP (has an `id`), the API is called immediately to update the package. Returns the API response.

Arguments:
* artifact : REQUIRED : The artifact ID (or name if `resolve=True`) to add
* artifactType : REQUIRED : The type of the artifact — must be one of the values in `ARTIFACT_TYPES`
* title : OPTIONAL : A human-readable title for the artifact
* resolve : OPTIONAL : If `True`, the method attempts to look up the artifact ID from the artifact name via the corresponding AEP service API. Supported types: `PROFILE_SEGMENT`, `CATALOG_DATASET`, `REGISTRY_SCHEMA`, `REGISTRY_MIXIN`, `REGISTRY_DATATYPE`, `REGISTRY_CLASS`, `FLOW`. Default `False`.

```python
# Add by ID
pkgManager.addArtifact(
    artifact='27115daa-c92b-4f17-a077-d65ffeb0c525',
    artifactType='PROFILE_SEGMENT',
    title='My Audience'
)

# Add by name (resolve=True)
pkgManager.addArtifact(
    artifact='My Schema Title',
    artifactType='REGISTRY_SCHEMA',
    resolve=True
)
```

---

### deleteArtifact

Remove an artifact from the package.\
* If the package is **new** (status `"NEW"`), the artifact is removed from the local `artifacts` list.
* If the package **already exists** in AEP (has an `id`), the API is called immediately to delete the artifact from the package.

Arguments:
* artifact : REQUIRED : The artifact ID (or name if `resolve=True`) to remove
* artifactType : REQUIRED : The type of the artifact — must be one of the values in `ARTIFACT_TYPES`
* resolve : OPTIONAL : If `True`, resolves the artifact ID from its name before deletion. Supported types: same as `addArtifact`. Default `False`.

```python
pkgManager.deleteArtifact(
    artifact='27115daa-c92b-4f17-a077-d65ffeb0c525',
    artifactType='PROFILE_SEGMENT'
)
```

---

### updatePackageInfo

Update the metadata of an **existing** package (name, description, or expiry).\
Raises a `ValueError` if the package has not been created yet (status `"NEW"`).\
Arguments:
* name : OPTIONAL : The new name of the package
* description : OPTIONAL : The new description of the package
* expiry : OPTIONAL : New expiry, either an integer (days from now) or ISO 8601 string

```python
pkgManager.updatePackageInfo(
    name='Renamed Package',
    description='Updated description',
    expiry=180
)
```

---

### createPackage

Push the locally defined package to AEP via a POST request.\
On success, the instance attributes `id`, `status`, and `package` are updated with the values returned by the API.

Returns the API response dictionary.

```python
response = pkgManager.createPackage()
print(pkgManager.id)     # now populated
print(pkgManager.status) # e.g. "DRAFT"
```

---

### publishPackage

Publish the package to make it available for import into other sandboxes.\
This is a **required step** before importing the package into a target sandbox.\
Raises a `ValueError` if the package has not been created yet.

Returns the API response dictionary.

```python
pkgManager.publishPackage()
```

A typical workflow is:
1. `createPackage()` — status becomes `"DRAFT"`
2. `publishPackage()` — package is exported and becomes ready for import

---

### publishPackagePublic

Change the package visibility from private (default) to public, enabling cross-organisation sharing.\
Raises a `ValueError` if the package is still in `"NEW"` or `"DRAFT"` state.

```python
pkgManager.publishPackagePublic()
```

---

## Artifact types reference

The following artifact types are supported and available via the `ARTIFACT_TYPES` attribute:

| Artifact Type | AEP Product | Object |
| --- | --- | --- |
| `PROFILE_SEGMENT` | Customer Data Platform | Audiences / Segments |
| `JOURNEY` | Adobe Journey Optimizer | Journeys |
| `CATALOG_DATASET` | Customer Data Platform | Datasets |
| `REGISTRY_SCHEMA` | Customer Data Platform | Schemas |
| `REGISTRY_MIXIN` | Customer Data Platform | Field Groups |
| `REGISTRY_DATATYPE` | Customer Data Platform | Data Types |
| `REGISTRY_DESCRIPTOR` | Customer Data Platform | Descriptors |
| `REGISTRY_CLASS` | Customer Data Platform | Classes |
| `IDENTITY_NAMESPACE` | Customer Data Platform | Identity Namespaces |
| `FLOW` | Customer Data Platform | Source Dataflows |
| `DULE_CONSENT_POLICY` | Customer Data Platform | Consent Policies |
| `DULE_GOVERNANCE_POLICY` | Customer Data Platform | Governance Policies |
| `CAMPAIGN` | Adobe Journey Optimizer | Campaigns |
| `CUSTOM_ACTION` | Adobe Journey Optimizer | Custom Actions |
| `CONTENT_TEMPLATE` | Adobe Journey Optimizer | Content Templates |
| `FRAGMENT` | Adobe Journey Optimizer | Fragments |
| `CHANNEL_CONFIGURATION` | Adobe Journey Optimizer | Channel Configurations |
| `DECISIONING_OBJECT` | Adobe Journey Optimizer | Decisioning Objects |

---

## Workflow examples

### Full export and import workflow

```python
import aepp
from aepp import sandboxes

# Connect to the SOURCE sandbox
sourceSandbox = aepp.importConfigFile('myconfig.json', sandbox='source-sandbox', connectInstance=True)

# 1. Build a partial package
pkgManager = sandboxes.PackageManager(
    config=sourceSandbox,
    name='My Migration Package',
    description='Schema and Segment for migration',
    packageType='PARTIAL',
    expiry=30
)

# 2. Add artifacts by ID
pkgManager.addArtifact('abc123', 'REGISTRY_SCHEMA', title='My Schema')
pkgManager.addArtifact('def456', 'PROFILE_SEGMENT', title='My Audience')

# 3. Create and publish
pkgManager.createPackage()
print(f"Package created with ID: {pkgManager.id}")

pkgManager.publishPackage()
print(f"Package status: {pkgManager.status}")

# 4. Import into the target sandbox using the Sandboxes class
sandboxInstance = sandboxes.Sandboxes(config=sourceSandbox)

# Optional: check for conflicts first
conflicts = sandboxInstance.importPackageCheck(
    packageId=pkgManager.id,
    targetSandbox='target-sandbox'
)

# Import (pass alternatives to map conflicting artifacts)
sandboxInstance.importPackage(
    packageId=pkgManager.id,
    targetSandbox='target-sandbox'
)
```

### Add artifact by name (resolve)

```python
import aepp
from aepp import sandboxes

mySandbox = aepp.importConfigFile('myconfig.json', sandbox='mysandbox', connectInstance=True)

pkgManager = sandboxes.PackageManager(config=mySandbox, name='Resolved Package')

# Resolve the schema ID from its title automatically
pkgManager.addArtifact(
    artifact='My XDM Individual Profile Schema',
    artifactType='REGISTRY_SCHEMA',
    resolve=True
)

pkgManager.createPackage()
```
