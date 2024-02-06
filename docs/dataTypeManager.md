# DataTypeManager for AEP Schema

This module is a custom module built by Adobe Consulting team in order to improve efficiency of the Data Type manipulation, documentation and analysis.\
The Field Group Manager is built on top of all of the existing [AEP Schema Registry API](https://developer.adobe.com/experience-platform-apis/references/schema-registry/), and [Schema class](./schema.md).

It is important to understand that a Field Group is built by using different data types. 
The native data types are : 
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

These native data types can be manipulated directly via the Field Groups.\
The more complex representation, that represents multiple fields, are called complex Data Type.\

If you were to create some, that are custom, you can use the DataTypeManager to modify and manipulate them programatically.\

A modification to a Data Type will have repercussion in all the schemas and field groups that are using this data type.


## Menu
- [Instantiation](#instantiation)
- [Data Type Manager methods](#data-type-manager-methods)

## Instantiation

The SchemaManager is a class that can be instantiated with different parameters.
Arguments:
* dataType : OPTIONAL : Either a data type id ($id or altId) or the data type dictionary itself.
    If dataType Id is passed, you need to provide the schemaAPI connection as well.
* title : OPTIONAL : to set or override the title (default None, use the existing title or do not set one for new data type) 
* schemaAPI : OPTIONAL : It is required if $id or altId are used. It is the instance of the `Schema` class.
* config : OPTIONAL : The config object in case you want to override the last configuration loaded.

code example:

```python
import aepp
from aepp import schema

prod = aepp.importConfigFile('myConfig.json',connectInstance=True,sandbox='prod')

schemaInstance = schema.Schema(config=prod)

myDataTypes = schemaInstance.getDataTypes()
## Selection of a data type
myDataType = 'https://ns.adobe.com/tenant/datatypes/257370e5e265b90a2f71341bead54cd5d46c10fd14e'

dataTypeManager = schema.DataTypeManager(myDataType,config=prod)

```

You can also use the `FieldGroupManager` `getDataTypeManager` method [see FieldGroupManager](./fieldGroupManager.md#getdatatypemanager)

The same way that what has been offer for Schema or Field Group, you can also instantiate a new `DataTypeManager` class without any definition, and create one from scratch with the methods provided.

Example code: 

```python
import aepp
from aepp import schema

prod = aepp.importConfigFile('myConfig.json',connectInstance=True,sandbox='prod')
dataTypeManager = schema.DataTypeManager(config=prod)

```



## Data Type Manager methods

The following methods are available on your `DataTypeManager` instance.

### setTitle
Set the title on the Data Type description
Argument:
* title : REQUIRED : The title to be set

### getField
Returns the field definition you want want to obtain.
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
Search for an attribute on the field of the data type.\
Returns either the list of fields that match this search or their full definitions.\
Arguments:
* attr : REQUIRED : a dictionary of key value pair(s).  Example : {"type" : "string"}\
    NOTE : If you wish to have the array type on top of the array results, use the key "arrayType".\
    Example : {"type" : "array","arrayType":"string"}\
            This will automatically set the joinType to "inner". Use type for normal search. 
* regex : OPTIONAL : if you want your value of your key to be matched via regex.\
    Note that regex will turn every comparison value to string for a "match" comparison.
* extendedResults : OPTIONAL : If you want to have the result to contain all details of these fields. (default False)
* joinType : OPTIONAL : If you pass multiple key value pairs, how do you want to get the match.
  * outer : provide the fields if any of the key value pair is matched.
  * inner : provide the fields if all the key value pair matched.

### addFieldOperation
Return the operation to be used on the data type with the Patch method (patchDataType), based on the element passed in argument.\
Arguments:
* path : REQUIRED : path with dot notation where you want to create that new field.\
    In case of array of objects, use the "[]{}" notation
* dataType : REQUIRED : the field type you want to create\
    A type can be any of the following: "string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object","array"\
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
Add the field to the existing Data Type definition.\
Returns False when the field could not be inserted.\
Arguments:
* path : REQUIRED : path with dot notation where you want to create that new field. New field name should be included.
* dataType : REQUIRED : the field type you want to create\
    A type can be any of the following: "string","boolean","double","long","integer","short","byte","date","dateTime","boolean","object","array"\
    NOTE : "array" type is to be used for array of objects. If the type is string array, use the boolean "array" parameter.
* title : OPTIONAL : if you want to have a custom title.
* objectComponents: OPTIONAL : A dictionary with the name of the fields contain in the "object" or "array of objects" specify, with their typed.\
    Example : {'field1:'string','field2':'double'}
* array : OPTIONAL : Boolean. If the element to create is an array. False by default.
* enumValues : OPTIONAL : If your field is an enum, provid a dictionary of value and display name, such as : {'value':'display'}
* enumType: OPTIONAL: If your field is an enum, indicates whether it is an enum (True) or suggested values (False)\
possible kwargs:
* defaultPath : Define which path to take by default for adding new field on tenant. Default "property", possible alternative : "customFields"

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
* save : OPTIONAL : If you wish to save it with the title used by the field group.\
    save as csv with the title used. Not title, used "unknown_fieldGroup_" + timestamp.
* description : OPTIONAL : If you want to have the description used (default False)
* xdmType : OPTIONAL : If you want to retrieve the xdm Data Type (default False)

### to_xdm
Return the Data Type definition as XDM

### updateDataType
Update the Data Type with the modification done before.\
It uses the PUT method, replacing previous definition.

### createDataType
Use the POST method to create the Data Type in the organization.

