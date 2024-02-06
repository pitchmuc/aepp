# FieldGroupManager for AEP Schema

This module is a custom module built by Adobe Consulting team in order to improve efficiency of the Field Groups Manipulation, Documentation and Analysis.\
The Field Group Manager is built on top of all of the existing [AEP Schema Registry API](https://developer.adobe.com/experience-platform-apis/references/schema-registry/), and [Schema class](./schema.md).

It is important to understand that a Schema is built by aggregating different field groups within a class.\
Therefore, when modifying the schema, what happens in the back-end is often a modification of the Field Group.

## Menu
- [Instantiation](#instantiation)
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

In the end these different parameters offer you different options to use the Field Group Manager.

### 1 Connecting to an existing Field Group

In this case, you can either the `schemaAPI` parameter or the `config` parameter.\
If this is your use-case, you can adapt the following code below:

```python
import aepp
from aepp import schema

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
mySchemaInstance = schema.Schema(config=mySandbox)

myfgs = mySchemaInstance.getFieldGroups()

singleFG = mySchemaInstance.data.fieldGroup_altId['titleOfFieldGroup']
### singleFG will be the altId of that `titleOfFieldGroup` field group

## option 1 : via schemaAPI parameter
fgManager = schema.FieldGroupManager(singleFG,schemaAPI=mySchemaInstance)

## option 2 : via config parameter
fgManager = schema.FieldGroupManager(singleFG,config=mySandbox)

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
fgManager = schema.SchemaManager(title='my Field Group Title', schemaAPI=mySchemaInstance)## setting a title now

## option 2
fgManager = schema.SchemaManager(config=mySandbox)

```

## Field Group Manager methods

The different methods available for Field Group Manger will be available below.

### setTitle
Set a name for the Field Group.\
Arguments:
* title : REQUIRED : a string to be used for the title of the FieldGroup

### getField
Returns the field definition you want want to obtain.\
Arguments:
* path : REQUIRED : path with dot notation to which field you want to access


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
Returns False when the field could not be inserted.\
Arguments:
* path : REQUIRED : path with dot notation where you want to create that new field. New field name should be included.
* dataType : REQUIRED : the field type you want to create
    A type can be any of the following: "string","boolean","double","long","integer","number","short","byte","date","dateTime","boolean","object","array"
    NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
* title : OPTIONAL : if you want to have a custom title.
* objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.
    Example : {'field1:'string','field2':'double'}
* array : OPTIONAL : Boolean. If the element to create is an array. False by default.
* enumValues : OPTIONAL : If your field is an enum, provid a dictionary of value and display name, such as : {'value':'display'}
* enumType: OPTIONAL: If your field is an enum, indicates whether it is an enum (True) or suggested values (False)\
possible kwargs:
* defaultPath : Define which path to take by default for adding new field on tenant. Default "property", possible alternative : "customFields"
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
* editable : OPTIONAL : If you can manipulate the structure of the field groups (default False)

### to_xdm
Return the fieldgroup definition as XDM

### getDataTypeManager
Retrieve the Data Type Manager instance of custom data type\
Argument:
* dataType : REQUIRED : id or name of the data type.

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
Use the POST method to create the field group in the organization.

### importFieldGroupDefinition
Importing the flat representation of the field group. It could be a dataframe or a CSV file containing the field group element.\
The field group needs to be editable to be updated.\
Argument:
* fieldGroup : REQUIRED : The dataframe or csv of the field\
    It needs to contains the following columns : "path", "type", "fieldGroup"
* sep : OPTIONAL : In case your CSV is separated by something else than comma. Default (',')
* sheet_name : OPTIONAL : In case you are uploading an Excel, you need to provide the sheet name

Example of a table used for creating a new schema

| path | type | fieldGroup | title | 
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