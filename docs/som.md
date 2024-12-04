# Simplified Object Manager

The Simplified Object Manager (SOM) is a library originally created in JavaScript and that has been ported to python for usage with other modules of the aepp library.\
Its idea is to simplify the creation of dictionary object, or JSON payload.

This library can be used to create XDM payload, or to easily read these XDM payload.

## Simplified Object Manager class

The Simplified Object Manager has been added in the `som` module.\
Contrary to most of the other module, it does not have any direct relationship with the AEP API.\
Therefore there is no need to upload a configuration to start using it.

```py
import aepp
from aepp import som

mySom = som.Som()

```

When instanciating the Som object, you can already pass a dictionary in the `data` argument, that could be an XDM dictionary, such as:

```py
mySom = som.Som(data={'my':{'data':'foo'}})
```

There is also an additional argument that you can use:

* `options` : OPTIONAL : A dictionary that possess one or multiple of the following keys
  * `defaultValue` : When accessing elements of the SOM, you can specify a fallback value that is being returned when the element is not defined. If the `defaultValue` is not defined, Som will return `None`.
  * `deepcopy` : By default, the data that you are passing in the data argument of SOM is deepcopied. If you wish to change that behavior, you need to pass `False` to this key.
  * `stack` : If you want to create a stack of the actions that has been executed on the Som object. It will create an attribute on the Som object, called stack, that is the list of all actions executed.

## Som methods

The Simplified Object Manager contains the following methods once instantiated.

### assign
Assign a value to the path provided.\
Arguments:
* path : REQUIRED : The string path with a dot notation to create the complex data structure that will hold the value.\
  If you want use an array as part of your build, you would need to use the following notation : `[0]`, where 0 is the element of the array to be used.
* value : REQUIRED : The value to be passed on that path.
* fallback : OPTIONAL : In case your assignment is dynamic and its value is `None`, you can avoid writing `None` in the Som object by passing a fallback value that will be used instead.
* params : OPTIONAL : A dictionary of options that could be one of the following:
  * type : You can cast the type you want your data you are passing as a value to be. Support `set`,`list` and `tuple`
  * override : You can decide to overwrite if any previous value already exist in that path.\
  The default behavior for list, tuple and set are the following:
    * `list` : assigning a new value to an existing list will append that value to that list
    * `set` : assigning a new value to an existing set will add that value to that set
    * `tuple` : assigning a new value to a tuple will override the tuple value (Tuple cannot be extended by nature) 

Examples:\
In all example below, we assumed you have instantiated the Som as the following.

```py
from aepp import som
mySom = som.Som()
```

#### Simple assignment

```py
mySom.assign('data.string','value1')
## it will output

{
  "data": {
    "string":"value1"
  }
}
```

#### Array assignment

```py
mySom.assign('data.array.[0]','val1')
## it will output
{
  "data": {
    "array":["val1"]
  }
}
mySom.assign('data.array.[1]','val2')
## it will now be
{
  "data": {
    "array":["val1","val2"]
  }
}
mySom.assign('data.array.[1]','val3')
## it will now be
{
  "data": {
    "array":["val1","val3"]
  }
}
```

#### Assignment deepdive
As you may have seen with the examples, the assignment capability is using pre-defined behavior to deal with merging different type.\
In order to help the understanding, I created the table below to see how the data will be treated, depending their type.\

The most unorthodox behavior would concern the `tuple`, that are ummutable per nature, so they have different behavior than the `list` and `set` type.

| assignment | som original data type | data type of the assignment | expected type after assignment | comment |
| -- | --  | -- | -- | -- |
| som.assign('path','str') | None | string | string |  |
| som.assign('path',4) | None| integer | integer |  |
| som.assign('path',1.5) | None | float | float |  |
| som.assign('path',[1,2]) | None | list | list |  |
| som.assign('path',(1,2)) | None | tuple | tuple |  |
| som.assign('path',set([1,2])) | None | set | set |  |
| som.assign('path','str') | list | list |  |
| som.assign('path',4) | list | list |  |
| som.assign('to_list',1.5) | list | list | data is appended |
| som.assign('to_list',[1,2]) | list | list | The list will be appended, it is not deconstructed. See `merge` for that behavior |
| som.assign('to_list',(1,2)) | list | list | tuple will be appended, it is not deconstructed. See `merge` for that behavior |
| som.assign('to_list',set([1,2])) | list | list | set will be appended, it is not deconstructed. See `merge` for that behavior |
| som.assign('to_tuple',1.5) | tuple | new data type | tuple are immutable, therefore are not modified and they are overriden |
| som.assign('to_list',[1,2]) | list | list | The list will be appended, it is not deconstructed. See `merge` for that behavior |
| som.assign('to_list',(1,2)) | list | list | tuple will be appended, it is not deconstructed. See `merge` for that behavior |
| som.assign('to_list',set([1,2])) | list | list | set will be appended, it is not deconstructed. See `merge` for that behavior |



### get
Retrieve the data based on the dot notation passed.\
If you want to return everything, use it without any parameter.\
Arguments:
* path : OPTIONAL : The dot notation path that you want to return. You can pass a list of path and the first match is returned.
* fallback : OPTIONAL : Temporary fallback if the dot notation path is not matched and you do not want to get the defaultValue

it is important to note that the array elements can be accessed by their numbers.

Example: having a structure as such

```py
{
  "data":{
    "string":"value1",
    "nested":{
      "string":"value2"
    }
  
  }
}
```


### merge
Merge a dictionary object with the existing Som data.\
Arguments:
* path : OPTIONAL : The path as dot notation where the merge should happen
* data : REQUIRED : The data to be merged with the existing Som data


### to_dict
Return the data hosted in the Som instance as a deep copy dictionary

### to_dataframe
Return the data as flatten dataframe
Arguments:
* expand_arrays : OPTIONAL : Default `False`, if set to `True`, it will create multiple rows for the arrays elements.