# Synchronizer

The `synchronizer` is a sub module that lives on top of several sub modules of aepp (schema, schemamanger,fieldgroupmanager, datatypemanager, classmanager, catalog, identity).

The module is intended to create or update elements between sandboxes within an organization.
The current supported artifacts for the synchronization job are: 
* data type
* field group
* schema
* class
* descriptors
* identity
* datasets
* mergepolicy
* audience


## Synchronizer class

The `Synchronizer` class is part of the `synchronizer` module and it takes the following elements as a parameter: 
* baseSandbox : REQUIRED : name of the base sandbox
* targets : REQUIRED : list of target sandboxes name as strings
* config : REQUIRED : ConnectObject with the configuration. Make sure that the configuration of your API allows connection to all targeted sandboxes.
* region : OPTIONAL : region of the sandboxes. default is 'nld2', possible values are: "va7" or "aus5 or "can2" or "ind2"
* localFolder : OPTIONAL : if provided, it will use the local environment as the base. Default is False.
                If localFolder is provided, the baseSandbox and targets are not used, and the configuration is used to connect to the local environment.
                configuration to use local environment is a folder with the name of your sandbox, inside that folder there must a folder for each base component:
                - class
                - schema
                - fieldgroup
                - datatype
                - identity
                - dataset
                - descriptor
                - mergepolicy
                - audience

For more details on localFolder, see [local files usage](./localfilesusage.md)

### Synchronizer attributes

Once instantiated the synchronizer object will contains certain attributes: 
* baseConfig : the config object with the base sandbox configuration to connect to the base sandbox (a `ConnectInstance` [instance](/getting-started.md#the-connectInstance-parameter))
* dict_targetsConfig : A dictionary of the different target sandbox configuration object (children of `ConnectInstance` class)
* region : The region used for the Identity Management for the Target and base Sandbox
* dict_targetComponents : A dictionary of the target components that has been created. A cache mechanisme to optimize the future usage of these components in the future.
* syncIssues : A variable created when using syncAll method that shows the artifact that could not be migrated.


### Synchronizer methods: 

The following methods are available once you have instantianted the `Synchronizer` class.

#### syncComponent
Synchronize a component to the target sandbox(es).\
The component could be a string (name or id of the component in the base sandbox) or a dictionary with the definition of the component.\
If the component is a string, you have to have provided a base sandbox in the constructor.\
Arguments:
* component : REQUIRED : name or id of the component or a dictionary with the component definition
* componentType : OPTIONAL : type of the component (e.g. "schema", "fieldgroup", "datatypes", "class", "identity", "dataset", "mergepolicy", "audience"). Required if a string is passed.\
It is not required but if the type cannot be inferred from the component, it will raise an error. 
* verbose : OPTIONAL : if True, it will print the details of the synchronization process

#### syncAll
Synchronize all the components to the target sandboxes.\
**NOTE: This method only works based on a local folder. See [extractArtefacts](.main#extractSandboxArtifacts) or [extract_artifacts](cli.md#extract_artifacts) in the CLI method**\
It will synchronize the components in the following order: 
1. Identities
2. Data Types
3. Classes
4. Field Groups
5. Schemas
6. Datasets\
Because the `Merge Policies` and `Audiences` needs the dataset and schema to be enabled in the target sandbox, and the synchronizer does not currently support enabling them for UPS.\
They will not be synchronized with that method.\
**NOTE**: a variable `syncIssues` is available on the synchronizer instance to track the different issues that happened during the synchronization process. Each issue is a dictionary with the following keys:
   * component : name of the component that caused the issue
   * type : original type of the component (e.g. "schema", "dataset"). A schema can have an issue related to a FieldGroup or a DataType, however, the schema will be the component that will be tracked in the issue and the type will be "schema" with the details of the error in the error message. 
   * error : error message
  
Arguments:
* force : OPTIONAL : if True, it will force the synchronization of the components even if they already exist in the target sandbox. Works for Schema, FieldGroup, DataType and Class.
* verbose : OPTIONAL : if True, it will print the details of the synchronization process

##### Best Practices around syncAll
It is not recommended to sync all the artefacts from one sandbox to another sandbox.\
If done directly via `baseSandbox` configuration, everything will be tentatively sync. This is very expensive and may contain elements you do not want to sync, such as OOTB schema and datasets.

The best practice is to download all the artifacts that you want to sync into one folder.\
**Reminder**: All dependencies are resolved during the `extractArtifact` so extracting `datasets` will take care of extracting `schema`,`fieldgroup`,`datatype`,`descriptors`,`identities`

Once all wished artifacts are in your folder, you can use the `syncAll` with a specifc folder.

#### getSyncFieldGroupManager
Helper method to get the FieldGroupManager for a target sandbox.\
It searches through the component cache to see if the FieldGroupManager for the target sandbox is already instantiated.\
If not, it generate an error.
Arguments:
* fieldgroup : REQUIRED : Either $id, or name or alt:Id of the field group to get
* sandbox : REQUIRED : name of the sandbox to get the field group from

#### getDatasetName
Helper method to get the name of a dataset from its id in a specific sandbox.\
Arguments:
* datasetId : REQUIRED : id of the dataset to get
* sandbox : REQUIRED : name of the sandbox to get the dataset from

## Notes on Synchronization capabilities

The synchronization capabilities are very similar to the sandbox tooling.

Due to the potential issue with ID management, the synchronizer bases its capabilities on name of the artifact.\
It means that the **name** of the schema, class, field group, data type, dataset, identity namespace are used. 

As of today, the synchronization will realize the following operation for the different artifacts: 

Operation |Schema | Class | Field Groups | Data Type | Descriptors | Dataset | Identity | Merge Policy | Audiences | Tags
--| -- | -- | -- | -- | -- | -- | -- | -- | -- | -- |
Create | Supported | Supported | Supported | Supported | Supported | Supported | Supported | Supported | Supported | Supported |
Update | Supported | Supported | Supported | Supported | Suppported | Supported | - | - | Supported | Supported |
Delete | Not supported | Not supported | Not supported | Not supported | Not supported | Not supported | Not supported | Not supported | Not supported | Supported |

It is not supported to delete an artifact or delete a field in an Field Group or Data Type via the Synchronizer.\
The synchronizer only supports additive operations 

The synchronizer will automatically resolve the dependency to create the elements require for the artifact used.\
Example:\
Synchronizing a dataset will automatically synchronize the underlying schema and the different field groups.\
If the schema is in a relationship with another schema (lookup), the associated lookup schema will also be created and the associated created. (note: The dataset associated with the lookup schema won't be created)

### Create 

For all artifacts, if the element does not exist in the target sandbox, it will automatically create it.\
The synchronizer automatically resolves all dependencies, which mean that the associated elements Schema associated to a dataset, or field group associated to a schema or a data type associated to a field groups are automatically created as well.

As of today, the schema and datasets are not enabled for profile per default during creation.


### Update

The **Update** operation is provided the capacity to add new fields to `field groups` or `data type` in the base and replicate that change to the target change.\
The removal of fields are not supported as it could be a breaking change in the target sandboxes.

It also supports the addition of a field group to a `schema` and replicate that change to all target sandboxes.

Audiences can also be updated to reflect the changes made in the base sandbox.
If an audience is synchronized and it already exists in the target sandbox, the synchronizer will update the audience definition in the target sandbox to reflect the definition in the base sandbox.

### Notes on Merge Policies synchronization

When creating a merge policy, if the merge policy is of type `dataSetPrecedence`, the synchronizer will automatically map the dataset IDs from the base sandbox to the target sandbox.\
This means that the datasets used in the merge policy in the base sandbox will be created in the target sandbox for the merge policy creation to succeed.\
Additionally, if the dataset reference a schema that does not exist in the target sandbox, the synchronizer will also create the schema and its associated field groups and data types. 

**HOWEVER**, the datasets and schema artifacts will not be enabled for Profile automatically. If you want to enable them for profile, you need to do it manually after the synchronization.\
The synchronization of this merge policy will fail until these datasets are enabled for profile in the target sandbox.

### Notes on Audience synchronization

When creating an audience, the synchronizer will simply copy the audience definition from the base sandbox to the target sandbox.\
For the audience to be created properly, the fields used in the audience definition must exist in the target sandbox and the schema should have been enabled for Profile.\
If the fields or schema do not exist in the target sandbox, the audience creation will fail.

### Notes on Tag synchronization
The tag by themselves would not need to be synchronized as they are automatically created at Organization level.\
What is supported is the synchronization of the tags association to the different artifacts that support them: 
* datasets
* audiences

When the sync happen, if the base has less tags than the target, the target component will be updated to have the same tags as the base. If the base has more tags than the target, the new tags will be added to the target component.\

## Incoming features

* Profile enabling capabilities
* Data Prep Mappings


