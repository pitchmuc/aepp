# Local Storage usage in aepp

As the usage of aepp expanded in customer site, the need to require a connection to leverage local storage for artefacts, instead of always connect to the sandbox, was becoming an important need.\
The idea behind local Storage is to not get the resources directly from the sandbox API connection but be able to use a hard local copy.\
This is especially true for the 2nd layer of aepp methods and class (`SchemaManager`, `FieldGroupManager`, etc...).\
This element is also into consideration for building a continuous integration pipeline that does not rely on AEP state but on your local state.

## Menu
- [Local Storage usage in aepp](#local-storage-usage-in-aepp)
  - [Menu](#menu)
  - [Local Storage Requirements](#local-storage-requirements)
  - [Extracting the artefacts](#extracting-the-artefacts)
  - [Using the local storage](#using-the-local-storage)


## Local Storage Requirements

In order for `aepp` to be able to functions with all type of implementation, the need for standardization was important.\
Each client has a different implementation, however, the different type of artefacts that are available from AEP are clearly defined.\

In that case, we have defined a clear structure for the artefacts that are supported in aepp for local storage.\
The structure is as follow: 

sandbox_folder\
  \class
  \schema
  \fieldgroup
  \datatype
  \descriptor
  \identity
  \dataset


You could technically mixed different sandbox in one folder and the elements will be just appended to folder as their type is definde (schema in schema), however, it is not a best practice approach as sandbox environment should be kept different.

The creation of clearly defined structure is making the dependency between elements able to be handled in the different tools that `aepp` is providing (`SchemaManager`, `ClassManager`, `FieldGroupManager`, `DataTypeManager`, `Synchronizer`).

## Extracting the artefacts

As the structure of the folder is clearly defined, the file are also defined specifically for resolving dependencies.\
In that sense, we could not let the user defined the structure of the schema or field group to be downloaded.
For that purpose, we provided a capability in aepp to export the data. 

`extractSandboxArtefacts`: This method will take all compatible and supported elements contain in your sandbox and extract that in a local folder defined.\
It takes the following argument: 
* sandbox: REQUIRED: the instance of a ConnectObject that contains the sandbox information and connection.
* localFolder: OPTIONAL: the local folder where to extract the sandbox. If not provided, it will use the current working directory and name the    folder the name of the sandbox.
* region: OPTIONAL: the region of the sandbox (default: nld2). This is used to fetch the correct API endpoints for the identities. 
    Possible values: "va7","aus5", "can2", "ind2"

Example of usage: 
```py
import aepp

prod = aepp.importConfigFile('myconfig.json',sandbox='prod',connectInstance=True)
aepp.extractSandboxArtefacts(prod,localFolder='prodFolder',region='va7')
```

## Using the local storage

The local folder setup can be used in the following components of `aepp`:

### SchemaManager

In SchemaManager, you can use the local file folder in this way: 

```py
import aepp
from aepp import schemamanager

mySchema = schemamanager.SchemaManager('my-schema-id',localFolder='prodFolder')

```

### Field Group Manager

In FieldGroupManager, you can use the local file folder in this way: 

```py
import aepp
from aepp import fieldgroupmanager

myfieldgroup = fieldgroupmanager.FieldGroupManager('my-fieldgroup-id',localFolder='prodFolder')

```

### DataType Manager

In DataTypeManager, you can use the local file folder in this way: 

```py
import aepp
from aepp import daatatypemanager

myfieldgroup = daatatypemanager.DataTypeManager('my-data-type-id',localFolder='prodFolder')

```

### Synchronizer

In the synchronizer, you can also pass the folder that contains your artefact.\
Following the structure built from the `extractSandboxArtefacts` method, the dependencies and the definition of the elements can be found.
In order to use the local file setup, you cna do the following setup once you have ran the `extractSandboxArtefacts` method.

```py 
import aepp
from aepp import synchronizer

configSetup = aepp.importConfigFile('myconfig.json',sandbox='target-sandbox',connectInstance=True)

synchronizor = synchronizer.Synchronizer(targets=['target-sandbox1'],config=configSetup,localFolder='my-folder')

synchronizor.syncComponent('my-schema',componentType='schema',verbose=True)

```


