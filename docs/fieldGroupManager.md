# FieldGroupManager for AEP Schema

This module is a custom module built by Adobe Consulting team in order to improve efficiency of the Field Groups manipulation, documentation and analysis.\
The Field Group Manager is built on top of all of the existing [AEP Schema Registry API](https://developer.adobe.com/experience-platform-apis/references/schema-registry/), and [Schema class](./schema.md).

It is important to understand that a Schema is built by aggregating different field groups within a class.\
Therefore, when modifying the schema, what happens in the back-end is often a modification of the Field Group.

## Menu
- [Instantiation](#instantiation)
- [Field Group Manager attrbites](#field-group-manager-attributes)
- [Field Group Manager methods](#field-group-manager-methods)

## Instantiation

The `FieldGroupManager` is a class that can be instantiated with different parameters:

* fieldGroup : OPTIONAL : If you wish to load an existing field group. You can either pass:
  * fieldGroupId : The ID representing the Field Group
  * fieldGroup definition : The dictionary representing the fieldGroup\
  If your wish is to create a new schema from scratch, then you do not need to pass anything.
* title : OPTIONAL : If you wish to override or define the title of your schema.\ 
  For existing schema, when you pass a value on the `schema` parameter, the title is detected automatically.
* fg_class : OPTIONAL : A list of classes. By default, it will be using the `IndividualProfile` class **and** the `ExperienceEvent` class. Possible value: `record`
* schemaAPI : OPTIONAL : To connect to your sandbox, you can pass the instance of the `Schema` class you want.
* config : OPTIONAL : Recommended to pass a [`ConnectObject` instance](./getting-started.md#the-connectinstance-parameter) if you did not pass the schemaAPI. That would ensure the usage of the correct sandbox.
* description : OPTIONAL : If you want to add a description to your field group.


In the end these different parameters offer you different options to use the Field Group Manager.
**Since version 0.3.9**
**It is part of the `fieldgroupmanager` module**

### 1 Connecting to an existing Field Group

In this case, you can either the `schemaAPI` parameter or the `config` parameter.\
If this is your use-case, you can adapt the following code below:

```python
import aepp
from aepp import schema
from aepp import fieldgroupmanager

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
mySchemaInstance = schema.Schema(config=mySandbox)

myfgs = mySchemaInstance.getFieldGroups()

singleFG = mySchemaInstance.data.fieldGroup_altId['titleOfFieldGroup']
### singleFG will be the altId of that `titleOfFieldGroup` field group

## option 1 : via schemaAPI parameter
fgManager = fieldgroupmanager.FieldGroupManager(singleFG,schemaAPI=mySchemaInstance)

## option 2 : via config parameter
fgManager = fieldgroupmanager.FieldGroupManager(singleFG,config=mySandbox)

## option 3 : from the Schema instance
fgManager = mySchemaInstance.FieldGroupManager(singleFG)

```

### 2 Creating a new Field Group from scratch

In this case, we would still need to pass the configuration or the schema API instance.\
If this is your use-case, you can adapt the following code below:

```python
import aepp
from aepp import schema

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
mySchemaInstance = schema.Schema(config=mySandbox)

## option 1
fgManager = schema.FieldGroupManager(title='my Field Group Title', schemaAPI=mySchemaInstance)## setting a title now

## option 2
fgManager = schema.FieldGroupManager(config=mySandbox)

```
## Field Group Manager attributes

Once you have instantiated the field group manager you can access some attributes directly via this object.\
The attributes available are:

* EDITABLE : `True` if it can be modified directly via FieldGroupManager, `False` if contains custom DataType
* title : Title of the Field Group
* STATE : either "EXISTING" or "NEW"
* id : $id of the field group
* altId : meta:altId of the field Group
* dataTypes : Dictionary of dataType Id and their DataTypeManager

## Field Group Manager methods

The different methods available for Field Group Manager will be available below.

### setTitle
Set a name for the Field Group.\
Arguments:
* title : REQUIRED : a string to be used for the title of the FieldGroup

### setDescription
Set the description to the Field Group.\
Argument:
* description : REQUIRED : The description to be added

### getField
Returns the field definition you want want to obtain.\
Arguments:
* path : REQUIRED : path with dot notation to which field you want to access

### updateClassSupported
Update the "meta:intendedToExtend" attribute of the Field Group definition.\
Arguments: 
* classIds : REQUIRED : A list of class ID to support for that field group

### searchField
Search for a field name based the string passed.\
By default, partial match is enabled and allow case sensitivity option.\
Arguments:
* string : REQUIRED : the string to look for for one of the field
* partialMatch : OPTIONAL : if you want to look for complete string or not. (default True)
* caseSensitive : OPTIONAL : if you want to compare with case sensitivity or not. (default False)

### searchAttribute
Search for an attribute on the field of the field groups.\
Returns either the list of fields that match this search or their full definitions.\
Arguments:
* attr : REQUIRED : a dictionary of key value pair(s).  Example : {"type" : "string"} \
    NOTE : If you wish to have the array type on top of the array results, use the key "arrayType". Example : {"type" : "array","arrayType":"string"}\
            This will automatically set the joinType to "inner". Use type for normal search. 
* regex : OPTIONAL : if you want your value of your key to be matched via regex.\
    Note that regex will turn every comparison value to string for a "match" comparison.
* extendedResults : OPTIONAL : If you want to have the result to contain all details of these fields. (default False)
* joinType : OPTIONAL : If you pass multiple key value pairs, how do you want to get the match.\
    outer : provide the fields if any of the key value pair is matched.\
    inner : provide the fields if all the key value pair matched.


### addFieldOperation
Return the operation to be used on the field group with the Patch method (patchFieldGroup), based on the element passed in argument.\
Arguments:
* path : REQUIRED : path with dot notation where you want to create that new field.\
    In case of array of objects, use the "[]{}" notation
* dataType : REQUIRED : the field type you want to create\
    A type can be any of the following: "string","boolean","double","long","integer","number","short","byte","date","dateTime","boolean","object","array"\
    NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
* title : OPTIONAL : if you want to have a custom title.
* objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.\
    Example : {'field1':'string','field2':'double'}
* array : OPTIONAL : Boolean. If the element to create is an array. False by default.
* enumValues : OPTIONAL : If your field is an enum, provid a dictionary of value and display name, such as : {'value':'display'}
* enumType: OPTIONAL: If your field is an enum, indicates whether it is an enum (True) or suggested values (False)\
possible kwargs:
* defaultPath : Define which path to take by default for adding new field on tenant. Default "property", possible alternative : "customFields"
        
### addField
Add the field to the existing fieldgroup definition.\
Returns `False` when the field could not be inserted.\
Arguments:
* path : REQUIRED : path with dot notation where you want to create that new field. New field name should be included.
* dataType : REQUIRED : the field type you want to create
    A type can be any of the following: "string","boolean","double","long","int","integer","number","short","byte","date","datetime","date-time","boolean","object","array","dataType"
    NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
* title : OPTIONAL : if you want to have a custom title.
* objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.
    Example : {'field1:'string','field2':'double'}
* array : OPTIONAL : Boolean. If the element to create is an array. False by default.
* enumValues : OPTIONAL : If your field is an enum, provid a dictionary of value and display name, such as : {'value':'display'}
* enumType: OPTIONAL: If your field is an enum, indicates whether it is an enum (True) or suggested values (False)\
* ref : OPTIONAL : If you have selected "dataType" as your `datatype`, you should use this parameter to pass the reference.
possible kwargs:
* defaultPath : Define which path to take by default for adding new field on tenant. Default "customFields", possible alternative : "property".
* description : if you want to add a description on your field


### removeField
Remove a field from the definition based on the path provided.\
NOTE: A path that has received data cannot be removed from a schema or field group.\
Argument:
* path : REQUIRED : The path to be removed from the definition.

### to_dict
Generate a dictionary representing the field group constitution\
Arguments:
* typed : OPTIONAL : If you want the type associated with the field group to be given.
* save : OPTIONAL : If you wish to save the dictionary in a JSON file

### to_dataframe
Generate a dataframe with the row representing each possible path.\
Arguments:
* save : OPTIONAL : If you wish to save it with the title used by the field group.
    save as csv with the title used. Not title, used "unknown_fieldGroup_" + timestamp.
* queryPath : OPTIONAL : If you want to have the query path to be used.
* description : OPTIONAL : If you want to have the description used (default False)
* xdmType : OPTIONAL : If you want to have the xdmType also returned (default False)
* editable : OPTIONAL : If you can manipulate the structure of the field groups (default False) -> see [Editable](#editable-concept)
* excludeObjects : OPTIONAL : Boolean that remove the lines that are defining objects/nodes. Default `False`.
* required : OPTIONAL : Provide an extra column `required` to specify which fields are set as required

the `origin` column is automatically returned and is helping understanding if the field is  native in the field group or added to the field group via a dataType.  

### to_xdm
Return the fieldgroup definition as XDM

### to_som
Generate a Som instance of the dictionary. Helping the manipulation of the dictionary if needed. 
Documentation on [SOM](./som.md)

### to_pydantic
Generate a dictionary representing the field group constitution
Arguments:
* save : OPTIONAL : If you wish to save the dictionary in a JSON file
* origin : OPTIONAL : Needed to identify who is calling the method. Default is "self".\
possible kwargs:
* output_model_type : The model that is outputed, default PydanticV2BaseModel

### getDataTypeManager
Retrieve the Data Type Manager instance of custom data type\
Argument:
* dataType : REQUIRED : id or name of the data type.

### getDataTypePaths
Return a dictionary of the paths in the field groups and their associated data type reference.\
Such as `{'path':'name-of-datatype'}`

### patchFieldGroup
Patch the field group with the given operation.\
Arguments:
* operation : REQUIRED : The list of operation to realise.\
            Possible operaitons : add, remove, and replace

The operation can be represented like this:

```JSON
[
  {
    "op": "add",
    "path": "/definitions/property/properties/_{TENANT_ID}/properties/propertyCity",
    "value": {
      "title": "Property Country",
      "description": "The country where the property is located.",
      "type": "string"
    }
  }
]
```

### updateFieldGroup
Use the PUT method to push the current field group representation to AEP via API request.

Example:
```python
import aepp
from aepp import schema

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
fgManager = schema.FieldGroupManager('fieldGroupId')

fgManager.addField('_tenant.object.field','integer','titleOfTheField')
fgManager.updateFieldGroup() ## the new definition is sent to AEP

```

### createFieldGroup
Use the POST method to create the field group in the organization schema repository.\
This method push the local definition to Adobe Experience Platform, officially creating the field group in your sandbox.

### createDescriptorOperation
Support the creation of a descriptor operation for `'xdm:descriptorLabel'` descriptor type.\
Arguments:
* descType : REQUIRED : The type of descriptor to be created.
* completePath : REQUIRED : The path to be used for the descriptor.
* labels : OPTIONAL : A list of labels to be used for the descriptor.

### createDescriptor
Create a descriptor attached to that class bsaed on the creatorDescriptor operation provided.\
Arguments:
* descriptor : REQUIRED : The operation to add a descriptor to the schema.

### UpdateDescriptor
Update a descriptor with the put method. Wrap the putDescriptor method of the Schema class.\
Arguments:
* descriptorId : REQUIRED : The descriptor ID to be updated
* descriptorObj : REQUIRED : The new definition of the descriptor as a dictionary.


### importFieldGroupDefinition
Importing the flat representation of the field group. It could be a dataframe or a CSV file containing the field group element.\
The field group needs to be editable to be updated.\
Argument:
* fieldGroup : REQUIRED : The dataframe or csv of the field\
    It needs to contains the following columns : "path", "xdmType", "fieldGroup"
* sep : OPTIONAL : In case your CSV is separated by something else than comma. Default (',')
* sheet_name : OPTIONAL : In case you are uploading an Excel, you need to provide the sheet name

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

## EDITABLE concept

There is 2 way to build a field group.\ 
One is to add each of the fields manually and create the different nodes (object) by hand or with the API.\
You can use for that the different native fields of AEP (string, double, etc...).\
The other is to use a predefined set of fields, that are called Data Type.\
When you are using the Data Type field that are not the native ones, you are technically using an external reference in your field group, and this reference can be used in multiple places in your field group.\
Because it is then wrong, and not possible, to modify one of the reference and not the other, the Field Groups that return `False` to the `Editable` column cannot be edited via `FieldGroupManager`.\
These Data Type, that are representing more than one field, can be edited via the [DataTypeManager](./dataTypeManager.md), however, the same way than for Field Group, any modification in the Data Type will be repercuted to all Schema and Field Groups using this Data Type. 