# ClassManager for AEP Schema

This module is a custom module built by Adobe Consulting team in order to improve efficiency of the Class manipulation, documentation and analysis.\
The Field Group Manager is built on top of all of the existing [AEP Schema Registry API](https://developer.adobe.com/experience-platform-apis/references/schema-registry/), and [Schema class](./schema.md).

It is important to understand that a Schema is built by aggregating different field groups within a class.\
Therefore, when modifying the schema, what happens in the back-end is often a modification of the Field Group.

## Menu
- [Instantiation](#instantiation)
- [Class Manager attrbites](#class-manager-attributes)
- [Class Manager methods](#class-manager-methods)

## Instantiation

The `ClassManager` is a class that can be instantiated with different parameters:

* aepclass : OPTIONAL : If you wish to load an existing class.
* title : OPTIONAL : If you wish to override or define the title of your class.
* behavior : OPTIONAL : If you want to define which behavioral element it extends.\
                Default: 'https://ns.adobe.com/xdm/data/record', possible values: 'https://ns.adobe.com/xdm/data/time-series','https://ns.adobe.com/xdm/data/adhoc'
* schemaAPI : OPTIONAL : To connect to your sandbox, you can pass the instance of the `Schema` class you want.
* config : OPTIONAL : Recommended to pass a [`ConnectObject` instance](./getting-started.md#the-connectinstance-parameter) if you did not pass the schemaAPI. That would ensure the usage of the correct sandbox.
* description : OPTIONAL : If you want to add a description to your class

In the end these different parameters offer you different options to use the Field Group Manager.


### 1 Connecting to an existing Field Group

In this case, you can either the `schemaAPI` parameter or the `config` parameter.\
If this is your use-case, you can adapt the following code below:

```python
import aepp
from aepp import schema
from aepp import classmanager

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
mySchemaInstance = schema.Schema(config=mySandbox)

myClasses = mySchemaInstance.getClasses()

singleClass = [cl for cl in myClasses if cl['title'] == 'mytitle'][0]
### singleFG will be the altId of that `titleOfFieldGroup` field group

## option 1 : via schemaAPI parameter
fgManager = classmanager.ClassManager(singleFG,schemaAPI=mySchemaInstance)

## option 2 : via config parameter
fgManager = classmanager.ClassManager(singleFG,config=mySandbox)

```

### 2 Creating a new class from scratch

In this case, we would still need to pass the configuration or the schema API instance.\
If this is your use-case, you can adapt the following code below:

```python
import aepp
from aepp import schema
from aepp import classmanager

mySandbox = aepp.importConfigFile('myconfig.json',sandbox='mysandbox',connectInstance=True)
mySchemaInstance = schema.Schema(config=mySandbox)

## option 1
myClass = classmanager.ClassManager(title='my Class Title', schemaAPI=mySchemaInstance)## setting a title now

## option 2
myClass = classmanager.ClassManager(config=mySandbox)

```

## ClassManager attributes

Once you have instantiated the field group manager you can access some attributes directly via this object.\
The attributes available are:

* EDITABLE : `True` if it can be modified directly via ClassManager, `False` if native class
* title : Title of the class
* STATE : either "EXISTING" or "NEW"
* id : $id of the class
* altId : meta:altId of the field Group
* behavior : The behavior used to create the class

## ClassManager methods

The different methods available for ClassManager will be available below.

### setTitle
Set a name for the Class.\
Arguments:
* title : REQUIRED : a string to be used for the title of the class

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

        
### addField
Add the field to the existing class definition.\
Returns `False` when the field could not be inserted.\
Arguments:
* path : REQUIRED : path with dot notation where you want to create that new field. New field name should be included.
* dataType : REQUIRED : the field type you want to create
    A type can be any of the following: "string","boolean","double","long","integer","number","short","byte","date","dateTime","boolean","object","array","dataType"
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
NOTE: A path that has received data cannot be removed from a class.\
Argument:
* path : REQUIRED : The path to be removed from the definition.

### to_dict
Generate a dictionary representing the class constitution\
Arguments:
* typed : OPTIONAL : If you want the type associated with the class to be given.
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

### to_xdm
Return the class definition as XDM

### to_pydantic
Generate a dictionary representing the field group constitution\
Arguments:
* save : OPTIONAL : If you wish to save the dictionary in a JSON file
* origin : OPTIONAL : If you want to specify the origin of the class.\
possible kwargs:
* output_model_type : The model that is outputed, default PydanticV2BaseModel

### createClass
Create the custom classs

## EDITABLE concept

If a class is native (`IndividualProfile` or `ExperienceEvent`), the class definition can not be changed. The EDITABLE attribute will be set to `False`.
If the class is a custom class, you can change and add attributes to it.