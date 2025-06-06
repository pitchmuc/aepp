# Synchronizer (BETA)

The `synchronizer` is a sub module that lives on top of several sub modules of aepp (schema, schemamanger,fieldgroupmanager, datatypemanager, classmanager, catalog, identity).\
**NOTE** : The synchronizer module is currently a **work in progress** and is expected to support more capabilities in the future. Some elements could change in the future and the module is not stable since stated otherwise here. 

The module is intended to create or update elements between sandboxes within an organization.
The current supported artefacts for the synchronization job are: 
* data type
* field group
* schema
* class
* descriptors
* identity
* datasets


## Synchronizer class

The `Synchronizer` class is part of the `synchronizer` module and it takes the following elements as a parameter: 
* baseSandbox : REQUIRED : name of the base sandbox
* targets : REQUIRED : list of target sandboxes name as strings
* config : REQUIRED : ConnectObject with the configuration. Make sure that the configuration of your API allows connection to all targeted sandboxes.
* region : OPTIONAL : region of the sandboxes. default is 'nld2', possible values are: "va7" or "aus5 or "can2" or "ind2"
* localEnvironment : OPTIONAL : if True, it will use the local environment. Default is False. ## WIP

### Synchronizer attributes

Once instantiated the synchronizer object will contains certain attributes: 
* baseConfig : the config object with the base sandbox configuration to connect to the base sandbox (a `ConnectInstance` [instance](/getting-started.md#the-connectInstance-parameter))
* dict_targetsConfig : A dictionary of the different target sandbox configuration object (children of `ConnectInstance` class)
* region : The region used for the Identity Management for the Target and base Sandbox
* dict_targetComponents : A dictionary of the target components that has been created. A cache mechanisme to optimize the future usage of these components in the future. 


### Synchronizer methods: 

The following methods are available once you have instantianted the `Synchronizer` class.

#### syncComponent
Synchronize a component to the target sandbox(es).\
The component could be a string (name or id of the component in the base sandbox) or a dictionary with the definition of the component.\
If the component is a string, you have to have provided a base sandbox in the constructor.\
Arguments:
* component : REQUIRED : name or id of the component or a dictionary with the component definition
* componentType : OPTIONAL : type of the component (e.g. "schema", "fieldgroup", "datatypes", "class", "identity", "dataset"). Required if a string is passed.\
It is not required but if the type cannot be inferred from the component, it will raise an error. 
* verbose : OPTIONAL : if True, it will print the details of the synchronization process


## Notes on Synchronization capabilities

The synchronization capabilities are very similar to the sandbox tooling.

Due to the potential issue with ID management, the synchronizer bases its capabilities on name of the artefact.\
It means that the **name** of the schema, class, field group, data type, dataset, identity namespace are used. 

As of today, the synchronization will realize the following operation for the different artefacts: 

Operation |Schema | Class | Field Groups | Data Type | Descriptors | Dataset | Identity | Tags |
--| -- | -- | -- | -- | -- | -- | -- | -- |
Create | Supported | Supported | Supported | Supported | Supported | Supported | Supported | Planned |
Update | Supported | Supported | Supported | Supported | Suppported | - | - | Planned |
Delete | Not supported | Not supported | Not supported | Not supported | Not supported | Not supported | Not supported | Not Supported |

It is not supported to delete an artefact or delete a field in an Field Group or Data Type via the Synchronizer.\
The synchronizer only supports additive operations 

The synchronizer will automatically resolve the dependency to create the elements require for the artefact used.\
Example:\
Synchronizing a dataset will automatically synchronize the underlying schema and the different field groups.\
If the schema is in a relationship with another schema (lookup), the associated lookup schema will also be created and the associated created. (note: The dataset associated with the lookup schema won't be created)

### Create 

For all artefacts, if the element does not exist in the target sandbox, it will automatically create it.\
The synchronizer automatically resolves all dependencies, which mean that the associated elements Schema associated to a dataset, or field group associated to a schema or a data type associated to a field groups are automatically created as well.

As of today, the schema and datasets are not enabled for profile per default during creation.


### Update

The **Update** operation is provided the capacity to add new fields to `field groups` or `data type` in the base and replicate that change to the target change.\
The removal of fields are not supported as it could be a breaking change in the target sandboxes.

It also supports the addition of a field group to a schema and replicate that change to all target sandboxes.


## Incoming features

* Tags (dataset)
* Audiences
* Local file system as source
* Profile enabling capabilities


