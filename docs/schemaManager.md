# SchemaManager for AEP Schema

This module is a custom module built by Adobe Consulting team in order to improve efficiency of the Schema Manipulation, Documentation and Analysis.\
The Schema Manager is built on top of all of the existing [AEP Schema Registry API](https://developer.adobe.com/experience-platform-apis/references/schema-registry/), and [Schema class](./schema.md).

## Menu
- [Instantiation](#instantiation)
- [Schema Manager attributs](#schema-manager-attributes)
- [Schema Manager methods](#schema-manager-methods)

## Instantiation

The SchemaManager is a class that can be instantiated with different parameters:

* schema : OPTIONAL : If you wish to load an existing schema. You can either pass:
  * schemaId : The ID representing the schema
  * schema definition : The dictionary representing the schema\
  If your wish is to create a new schema from scratch, then you do not need to pass anything.
* fieldGroups : OPTIONAL : if you wish to pass the list of field groups to be used in that schema.\
  You can pass a list of `fieldGroupId`, such as `[fieldGroupId1,fieldGroupId2]`
* title : OPTIONAL : If you wish to override or define the title of your schema.\ 
  For existing schema, when you pass a value on the `schema` parameter, the title is detected automatically.
* schemaClass : OPTIONAL : By default, it will be using the `IndividualProfile` class. You can also pass the `ExperienceEvent` class if you wish. The values would be for each:
  * `https://ns.adobe.com/xdm/context/profile` default Profile class
  * `https://ns.adobe.com/xdm/context/experienceevent` Experience Event class
* schemaAPI : OPTIONAL : To connect to your sandbox, you can pass the instance of the `Schema` class you want.
* config : OPTIONAL : Recommended to pass a [`ConnectObject` instance](./getting-started.md#the-connectinstance-parameter) if you did not pass the schemaAPI. That would ensure the usage of the correct sandbox.

In the end these different parameters offer you different options to use the schemaManager.

**Since version 0.3.9**
**It is part of the `schemamanager` module**

### 1 Connecting to an existing schema

In this case, you can either the `schemaAPI` parameter or the `config` parameter.\
If this is your use-case, you can adapt the following code below:

```python
import aepp
from aepp import schema
from aepp import schemamanager

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
mySchemaInstance = schema.Schema(config=mySandbox)

myschemas = mySchemaInstance.getSchemas()

singleSchema = mySchemaInstance.data.schema_altId['titleOfSchema']
### singleSchema will be the altId of that `TitleOfSchema` schema

## option 1 : via schemaAPI parameter
schemaManager = schemamanager.SchemaManager(singleSchema,schemaAPI=mySchemaInstance)

## option 2 : via config parameter
schemaManager = schemamanager.SchemaManager(singleSchema,config=mySandbox)

## option 3 : from the Schema instance
schemaManager = mySchemaInstance.SchemaManager(singleSchema)


```

### 2 Creating a new Schema based on existing field groups

If this is your use-case, you can adapt the following code below:

```python
import aepp
from aepp import schema
from aepp import schemamanager

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
mySchemaInstance = schema.Schema(config=mySandbox)

myFieldGroups = mySchemaInstance.getFieldGroups()
### defining the list of fieldGroupIds you want to use
### using some code and outputting the list such as:
listFGids = ['fgId1','fgId2','fgId2']

## option 1
schemaManager = schemamanager.SchemaManager(fieldGroups=listFGids,schemaAPI=mySchemaInstance)

## option 2
schemaManager = schemamanager.SchemaManager(fieldGroups=listFGids,config=mySandbox)

```

### 3 Creating a new Schema from scratch

In this case, we would still need to pass the configuration or the schema API instance.\
If this is your use-case, you can adapt the following code below:

```python
import aepp
from aepp import schema
from aepp import schemamanager

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
mySchemaInstance = schema.Schema(config=mySandbox)

## option 1
schemaManager = schemamanager.SchemaManager(title='my Schema Title', schemaAPI=mySchemaInstance)## setting a title now

## option 2
schemaManager = schemamanager.SchemaManager(config=mySandbox)

```
## Schema Manager attributes

Once you have instantiated the schema manager you can access some attributes directly via this object.\
The attributes available are:

* fieldGroupIds : a list of Field Group Ids
* fieldGroupsManagers : a dictionary of the Field group Name and their FieldGroupManager Instances
* title : Title of the Schema
* STATE : either "EXISTING" or "NEW"
* id : $id of the schema
* altId : meta:altId of the schema
* classId : Class Id associated with the Schema

## Schema Manager methods

There are several methods available once you have instantiated a `SchemaManager` class.\
Note that all of the modification done by using these methods are local until the `updateSchema` or `createSchema` are used.\
The methods will be described below.

### setTitle

This methods set a title to your schema, or override the existing one.\
Arguments:
* title : REQUIRED : a string to be used for the title of the Schema

### setDescription

Set the description to the Schema.\
Argument:
* description : REQUIRED : The description to be added

### searchField

Search for a field in the different field group.\
You would need to have set fgManager attribute during instantiation or use the convertFieldGroups\
Arguments:
* string : REQUIRED : The string you are looking for
* partialMatch : OPTIONAL : If you want to use partial match (default True)
* caseSensitive : OPTIONAL : If you want to remove the case sensitivity.

code example:

```python
import aepp
from aepp import schema
from aepp import schemamanager

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
schemaManager = schemamanager.SchemaManager('singleSchemaId',config=mySandbox)

res = schemaManager.searchField('myFieldName',partialMatch=True,caseSensitive=False)

# res will be showing this type of result
#[{'myFieldName': {'type': 'string',
#   'title': 'myFieldName',
#   'meta:xdmType': 'string',
#   'path': '_tenant.object.myFieldName',
#   'queryPath': '_tenant.object.myFieldName',
#   'completePath': '/definitions/property/properties/_tenant/properties/object/properties/myFieldName'}}]
```

This method is interesting to get the complete path and query path for API or Query Service setup.

### searchAttribute

Search for an attribute and its value based on the keyword\
Arguments:
* attr : REQUIRED : a dictionary of key value pair(s).  Example : {"type" : "string"} \
    NOTE : If you wish to have the array type, use the key "arrayType". Example : {"type" : "array","arrayType":"string"} 
* regex : OPTIONAL : if you want your value of your key to be matched via regex.\
    Note that regex will turn every comparison value to string for a "match" comparison.
* extendedResults : OPTIONAL : If you want to have the result to contain all details of these fields. (default False)
* joinType : OPTIONAL : If you pass multiple key value pairs, how do you want to get the match.\
    outer : provide the fields if any of the key value pair is matched. (default)\
    inner : provide the fields if all the key value pair matched.

### addFieldGroup
Add a field groups to field Group object and the schema.\ 
return the specific FieldGroup Manager instance.\
Arguments:
* fieldGroup : REQUIRED : The fieldGroup ID or the dictionary definition connecting to the API.
  if a fieldGroup ID is provided, you should have added a schemaAPI previously.

### getFieldGroupManager
Return a field group Manager of a specific name.\
Only possible if fgManager was set to True during instanciation.\
Argument:
* fieldgroup : REQUIRED : The title or the $id of the field group to retrieve.

[documentation on FieldGroupManager](./fieldGroupManager.md)

### to_dataframe
Extract the information from the Field Groups to a DataFrame.\
Arguments:
* save : OPTIONAL : If you wish to save it with the title used by the field group.\
    save as csv with the title used. Not title, used "unknown_schema_" + timestamp.
* queryPath : OPTIONAL : If you want to have the query path to be used.
* description : OPTIONAL : If you want to have the description added to your dataframe. (default False)
* xdmType : OPTIONAL : If you want to have the xdmType also returned (default False)
* editable : OPTIONAL : If you can manipulate the structure of the field groups (default False). More details on [Editable concept](#editable-concept)
* excludeObjects : OPTIONAL : Boolean that remove the lines that are defining objects/nodes. Default `False`.
* required : OPTIONAL : Provide an extra column `required` to specify which fields are set as required 

the `origin` column is automatically returned and is helping understanding if the field is related to the class, native in the field group or added to the field group via a dataType.  

### to_dict
Return a dictionary of the whole schema. You need to have instanciated the Field Group Manager

### to_som
Generate a Som instance of the dictionary. Helping the manipulation of the dictionary if needed. 
Documentation on [SOM](./som.md)

### createSchema
Send a createSchema request to AEP to create the schema.\
It removes the "$id" if one was provided to avoid overriding existing ID.

### updateSchema
Use the PUT method to replace the existing schema with the new definition.

### getDescriptors
Use to retrieve all descriptors associated to that schema.\
return a list.

### createDescriptorOperation
Create a descriptor object to be used in the createDescriptor.\
You can see the type of descriptor available in the DESCRIPTOR_TYPES attribute and also on the official documentation:
https://experienceleague.adobe.com/docs/experience-platform/xdm/api/descriptors.html?lang=en#appendix \
Arguments:
* descType : REQUIRED : The type to be used.\
    it can only be one of the following value: "xdm:descriptorIdentity","xdm:alternateDisplayInfo","xdm:descriptorOneToOne","xdm:descriptorReferenceIdentity","xdm:descriptorDeprecated","xdm:descriptorLabel","xdm:descriptorRelationship"
* completePath : REQUIRED : the dot path of the field you want to attach a descriptor to.\
    Example: '_tenant.tenantObject.field'
* identityNSCode : OPTIONAL : if the descriptor is identity related, the namespace CODE  used.
* identityPrimary : OPTIONAL : If the primary descriptor added is the primary identity.
* alternateTitle : OPTIONAL : if the descriptor is alternateDisplay, the alternate title to be used.
* alternateDescription : OPTIONAL if you wish to add a new description.
* lookupSchema : OPTIONAL : The schema ID for the lookup if the descriptor is for lookup setup
* targetCompletePath : OPTIONAL : if you have the complete path for the field in the target lookup schema.
* idField : OPTIONAL : If it touches a specific Field ID

### createDescriptor
Create a descriptor attached to that class bsaed on the creatorDescriptor operation provided.\
Arguments:
* descriptor : REQUIRED : The operation to add a descriptor to the schema.


### updateDescriptor
Update a descriptor with the put method. Wrap the putDescriptor method of the Schema class.\
Arguments:
* descriptorId : REQUIRED : The descriptor ID to be updated
* descriptorObj : REQUIRED : The new definition of the descriptor as a dictionary.


### compareObservableSchema
A method to compare the existing schema with the observable schema and find out the difference in them.\
It output a dataframe with all of the path, the field group, the type (if provided) and the part availability (in that dataset)\
Arguments:
* observableSchemaManager : REQUIRED : the ObservableSchemaManager class instance.

The `ObservableSchema` class is part of the [catalog API](./catalog.md).

### importSchemaDefinition
Import the definition of all the fields defined in csv or dataframe.\
Update all the corresponding field groups based on that.\
The update is local only, see following method to apply that change in your sandbox.\
Returns a dictionary such as {'fieldGroupName':'changeMadeByThatImport'}
Argument:
* schema : REQUIRED : The schema defined in the CSV.
    It needs to contains the following columns : "path", "xdmType", "fieldGroup","title"
* sep : OPTIONAL : If your CSV is separated by other character  than comma (,)
* sheet_name : OPTIONAL : If you are loading an Excel, please provide the sheet_name.


Example of a table used for creating a new schema

| path | xdmType | fieldGroup | title | 
| -- | -- | -- | -- |
|_tenant.object{} | object | fieldGroup1 | myObject|
|_tenant.object.field1 | string | fieldGroup1 | myField 1 |
|_tenant.object.arrayOfObject[]{} | object | fieldGroup1 | my Array of Object|
|_tenant.object.arrayOfObject[]{}.double1 | double | fieldGroup1 | my double |
|_tenant.object.arrayOfObject[]{}.stringArray[] | string | fieldGroup1 | my string array |

Supported type:
* "object": For nested JSON objects.
* "string": For textual data. 
* "integer": For whole numbers. 
* "number": For numeric values, including decimals.
* "double": For double-precision floating-point numbers
* "short": For short integer numbers.
* "long": For long integer numbers
* "boolean": For true/false values.
* "datetime": For date and time values. 
* "date": For date values.

As you can see, there are special notation for arrays and array of objects:\
**[]** at the end of the path notation will create this element (string, double) as array\
**[]{}** at the end of the path notation will create this element as array of objects.

the return of that method will be a dictionary that contains all field group as keys.\
You can then check for each field group if the change is showing the expecting values.
Once you are happy with the changes, you can apply these changes with the following method.

### applyFieldsChanges
Apply the changes that you have imported to the field groups and possible descriptors via the importSchemaDefinition\
It also update the references to the schema and add new field groups to the schema definition.\
**NOTE**: You will need to update the Schema in case of new field groups have been added.\
Returns a dictionary such as {'fieldGroupName':'{object returned by the action}'}\


## EDITABLE concept

A schema is always composed of Field Groups and there is 2 way to build a Field Group.\ 
One is to add each of the fields manually and create the different nodes (object) by hand or with the API.\
You can use for that the different native fields of AEP (string, double, etc...).\
The other is to use a predefined set of fields, that are called Data Type.\
When you are using the Data Type field that are not the native ones, you are technically using an external reference in your field group, and this reference can be used in multiple places in your field group.\
Because it is then wrong, and not possible, to modify one of the reference and not the other, the Field Groups that return `False` to the `Editable` column cannot be edited via Field Group Manager.\
These Data Type, that are representing more than one field, can be edited via the [DataTypeManager](./dataTypeManager.md), however, the same way than for Field Group, any modification in the Data Type will be repercuted to all Schema and Field Groups using this Data Type.