# Local Storage usage in aepp

As the usage of aepp expanded in customer site, the need to require a connection to leverage local storage for artifacts, instead of always connect to the sandbox, was becoming an important need.\
The idea behind local Storage is to not get the resources directly from the sandbox API connection but be able to use a hard local copy.\
This is especially true for the 2nd layer of aepp methods and class (`SchemaManager`, `FieldGroupManager`, etc...).\
This element is also into consideration for building a continuous integration pipeline that does not rely on AEP state but on your local state.

## Menu
- [Local Storage usage in aepp](#local-storage-usage-in-aepp)
  - [Menu](#menu)
  - [Local Storage Requirements](#local-storage-requirements)
      - [Strategy around folder extraction](#strategy-around-folder-extraction)
    - [Config File](#config-file)
  - [Extracting the artifacts](#extracting-the-artifacts)
  - [Using the local storage](#using-the-local-storage)
    - [SchemaManager](#schemamanager)
    - [Field Group Manager](#field-group-manager)
    - [DataType Manager](#datatype-manager)
    - [Synchronizer](#synchronizer)


## Local Storage Requirements

In order for `aepp` to be able to functions with all type of implementation, the need for standardization was important.\
Each client has a different implementation, however, the different type of artifacts that are available from AEP are clearly defined.\

In that case, we have defined a clear structure for the artifacts  that are supported in aepp for local storage.\
The structure is as follow: 

sandbox_folder\
  config.json\
  \class\
  \schema\
  \fieldgroup\
    \global\ for OOTB field Groups
  \datatype\
    \global\ for OOTB data type
  \descriptor\
  \identity\
  \dataset\
  \mergePolicy\
  \audience\
  \tag\

#### Strategy around folder extraction

You could technically mixed different sandbox in one folder and the elements will be just appended to folder as their type is definde (schema in schema), **however**, it is not a best practice approach as sandbox environment should be kept different as artefact could be overwritting each other.\

The synchronizer can reference more than one folder as the source, and you can have some global artefacts in a common folder and have specific sandbox artefacts in their respective folder.\ 

The creation of clearly defined structure is making the dependency between elements able to be handled in the different tools that `aepp` is providing (`SchemaManager`, `ClassManager`, `FieldGroupManager`, `DataTypeManager`, `Synchronizer`).

### Config File

In order to simplify the reading of the artifact when local folder is used, we are storing a `config.json` file in the main folder.\
This config is a dictionary that may evolve in the future, when more dependencies are built.\
Check the page regularly if additional information are set as requirement.

Current config setup: 
```JSON
{
  "imsOrgId":"your IMS Org ID",
  "tenantId":"your tenant ID starting with _",
  "sandbox":"your sandbox name used for extraction",
}
```


## Extracting the artifacts

As the structure of the folder is clearly defined, the file are also defined specifically for resolving dependencies.\
In that sense, we could not let the user defined the structure of the schema or field group to be downloaded.
For that purpose, we provided a capability in aepp to export the data. 

`extractSandboxArtifacts`: This method will take all compatible and supported elements contain in your sandbox and extract that in a local folder defined.\
It takes the following argument: 
* sandbox: REQUIRED: the instance of a ConnectObject that contains the sandbox information and connection.
* localFolder: OPTIONAL: the local folder where to extract the sandbox. If not provided, it will use the current working directory and name the    folder the name of the sandbox.
* region: OPTIONAL: the region of the sandbox (default: nld2). This is used to fetch the correct API endpoints for the identities. 
    Possible values: "va7","aus5", "can2", "ind2"

Example of usage: 
```py
import aepp

prod = aepp.importConfigFile('myconfig.json',sandbox='prod',connectInstance=True)
aepp.extractSandboxArtifacts(prod,localFolder='prodFolder',region='va7')
```


## Using the local storage

The local folder setup can be used in the following components of `aepp`:

**Note**: The localFolder arguments can take more than one folder, it will search in the order of the folders provided for the artifacts.

### SchemaManager

In SchemaManager, you can use the local file folder in this way: 

```py
import aepp
from aepp import schemamanager

mySchema = schemamanager.SchemaManager('my-schema-id',localFolder='prodFolder')

## or 

mySchema = schemamanager.SchemaManager('my-schema-id',localFolder=['prodFolder','commonArtifactsFolder'])

```

### Field Group Manager

In FieldGroupManager, you can use the local file folder in this way: 

```py
import aepp
from aepp import fieldgroupmanager

myfieldgroup = fieldgroupmanager.FieldGroupManager('my-fieldgroup-id',localFolder='prodFolder')

## or
myfieldgroup = fieldgroupmanager.FieldGroupManager('my-fieldgroup-id',localFolder=['prodFolder','commonArtifactsFolder'])

```

### DataType Manager

In DataTypeManager, you can use the local file folder in this way: 

```py
import aepp
from aepp import daatatypemanager

myfieldgroup = daatatypemanager.DataTypeManager('my-data-type-id',localFolder='prodFolder')

```

### Synchronizer

In the synchronizer, you can also pass the folders that contains your artifacts.\
Following the structure built from the `extractSandboxArtifacts` method, the dependencies and the definition of the elements can be found.
In order to use the local file setup, you cna do the following setup once you have ran the `extractSandboxArtifacts` method.

```py 
import aepp
from aepp import synchronizer

configSetup = aepp.importConfigFile('myconfig.json',sandbox='target-sandbox',connectInstance=True)

synchronizor = synchronizer.Synchronizer(targets=['target-sandbox1'],config=configSetup,localFolder='my-folder')
## or 
synchronizor = synchronizer.Synchronizer(targets=['target-sandbox1'],config=configSetup,localFolder=['my-folder','commonArtifactsFolder'])

synchronizor.syncComponent('my-schema',componentType='schema',verbose=True)

```



