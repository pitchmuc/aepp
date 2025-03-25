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
## mySom will now contain

{
  "data": {
    "string":"value1"
  }
}
```

Based on these principle you can extend your Som object with additional assignments

```py
mySom.assign('data.integer',10)
## mySom will now contain

{
  "data": {
    "string":"value1",
    "integer":10
  }
}
```

```py
mySom.assign('data.something.nested.float',1.0)
## mySom will now contain

{
  "data": {
    "string":"value1",
    "integer":10,
    "something":{
      "nested":{
        "float":1.0
        }
      }
  }
}
```



#### List assignment

You can find below some examples when manipulating `list` and the expected outcome of the operations.\
For demo, we imagine that it is based on an empty Som (`mySom`)

```py
mySom.assign('data.list.[0]','val1')
## mySom will output
{
  "data": {
    "list":["val1"]
  }
}
mySom.assign('data.list.[1]','val2')
## it will now be
{
  "data": {
    "list":["val1","val2"]
  }
}
mySom.assign('data.list.[1]','val3')
## it will now be
{
  "data": {
    "list":["val1","val3"]
  }
}
mySom.assign('data.list.[1]',('val4','val5'))
## it will now be
{
  "data": {
    "list":["val1","val3","val4","val5"]
  }
}

```

#### Set assignment

The `set` are sort of a list that cannot contain duplicate, they can be quite helpful.\
You can find below of some example operation made on `set` object.\
For demo, we imagine that it is based on an empty Som (`mySom`)

```py
mySom.assign('data.set',set(['val1']))
## it will output
{
  "data": {
    "set":["val1"]
  }
}
mySom.assign('data.set','val2')
## it will now be
{
  "data": {
    "set":["val1","val2"]
  }
}
mySom.assign('data.set',['val3','val4'])
## it will now be
{
  "data": {
    "set":["val1","val2","val3","val4"]
  }
}
```

#### Tuple assignment
The `tuple` are sort of a list that cannot be mutated. Their main reason to exist is to contain a data that cannot be modified.\
You can find below of some example operation made on `tuple` object.\
The `tuples` are really different than any iterable object and therefore their assignment support are different.
For demo, we imagine that it is based on an empty Som (`mySom`)

```py
mySom.assign('data.tuple',tuple(['val1']))
## it will output
{
  "data": {
    "tuple":["val1"]
  }
}
mySom.assign('data.tuple','val2')
## it will now be
{
  "data": {
    "tuple":["val1","val2"]
  }
}
mySom.assign('data.tuple',['val3','val4'])
## it will now be
{
  "data": {
    "tuple":["val1","val2","val3","val4"]
  }
}
```


#### Assignment deepdive
As you have seen with the previous examples, the assignment capability is using pre-defined behavior to deal with merging different type.\
In order to help the understanding, I created the table below to see how the data will be treated, depending their type.\

The most unorthodox behavior would concern the `tuple`, that are ummutable per nature, so they have different behavior than the `list` and `set` type.

| assignment | som original data type | data type of the assignment | expected type after assignment | comment |
| -- | --  | -- | -- | -- |
| `som.assign('path','str')` | None | string | string |  |
| `som.assign('path',4)` | None| integer | integer |  |
| `som.assign('path',1.5)` | None | float | float |  |
| `som.assign('path',[1,2])` | None | list | list |  |
| `som.assign('path',(1,2))` | None | tuple | tuple |  |
| `som.assign('path',set([1,2]))` | None | set | set |  |
| `som.assign('path','str')` | list | str | list |  |
| `som.assign('path',4)` | list | integer | list |  |
| `som.assign('to_list',1.5)` | list | float | list | data is appended to the list |
| `som.assign('to_list',[1,2])` | list | list | list | The list will be appended, it is not deconstructed. See `merge` for that behavior |
| `som.assign('to_list',(1,2))` | list | tuple | list | tuple will be appended, it is not deconstructed. See `merge` for that behavior |
| `som.assign('to_list',set([1,2]))` | list | set | list | set will be appended, it is not deconstructed. See `merge` for that behavior |
| `som.assign('to_set','something')` | set | string | set | The string will be appended to the set |
| `som.assign('to_set',1.5)` | set | float | set | The float will be appended to the set |
| `som.assign('to_set',[1,2])` | set | list  | set | The list will be deconstructed and each element added indidvidually to the set. |
| `som.assign('to_set',(1,2))` | set | tuple | set | The tuple will be deconstructed and each element added indidvidually to the set. |
| `som.assign('to_set',set([1,2]))` | set | set | set | The set will be deconstructed and each element added indidvidually to the set.|
| `som.assign('to_tuple','something')` | tuple | string | tuple | Tuples are immutable, therefore are not modified and they are overriden. The new value string will be the only value in that tuple. See `merge` for adding element to tuple. |
| `som.assign('to_tuple',1.5)` | tuple | float | tuple | Tuples are immutable, therefore are not modified and they are overriden. The new value float will be the only value in that tuple. See `merge` for adding element to tuple  |
| `som.assign('to_tuple',[1,2])` | tuple | list  | tuple | Tuples are immutable. The list values will replace the original tuple value(s). See `merge` for adding element to tuple |
| `som.assign('to_tuple',(1,2))` | tuple | tuple | tuple | Tuples are immutable. The new tuple value(s) will replace the old one(s). See `merge` for adding elements to tuple. |
| `som.assign('to_tuple',set([1,2]))` | tuple | set | tuple | Tuples are immutable. The new tuple value(s) will replace the old one(s). See `merge` for adding elements to tuple. See `merge` for that behavior |



### get
Retrieve the data based on the dot notation passed.\
If you want to return everything, use it without any parameter.\
Arguments:
* path : OPTIONAL : The dot notation path that you want to return. You can pass a list of path and the first match is returned.
* fallback : OPTIONAL : Temporary fallback if the dot notation path is not matched and you do not want to get the defaultValue

it is important to note that the array elements can be accessed by their numbers.

Example: having a structure as such

```py
test = {
  "data":{
    "string":"value1",
    "nested":{
      "string":"value2"
    }
  
  }
}

mysom = som.Som(test)

```

Examples of get method usage:

```py

mysom.get('data') ## returns {"string":"value1","nested":{"string":"value2"}}
mysom.get('data.string') ## returns "value1"
mysom.get('data.nested.string') ## returns "value2"
mysom.get('data.nested.somethingElse') ## returns None because "somethingElse" does not exist
mysom.get('data.nested.somethingElse','fallback') ## returns 'fallback' as "somethingElse" does not exist
```


### merge
Merge a dictionary or a specific `list`, `tuple` or `set` object with the existing Som data.\
Arguments:
* path : OPTIONAL : The path as dot notation where the merge should happen
* data : REQUIRED : The data to be merged with the existing Som data

#### Merging use-case

The merging operation is the only operation that deconstruct elements to `list`, and expand the `tuples`.\

Examples:

```py
mySom = som.Som({'myList':[1,2,3]})
mySom.assign('myList',[4,5,6])
# It will automatically create this structure
{"myList":[1,2,3,[4,5,6]]}

mySom = som.Som({'myList':[1,2,3]})
mySom.merge('myList',[4,5,6])
# It will automatically create this structure
{"myList":[1,2,3,4,5,6]}

```

The merge operation is the only operation that can append elements to an existing `tuple`.\
Tuples are immutable and therefore the default behavior of the assignment is to replace the existing value(s) with the new value(s) provided.\
If you want to extend the tuple value(s) you can use the merge operation

```py
mySom = som.Som({'myTuple':(1,2,3)})
mySom.assign('myTuple',(4,5,6))
# It will automatically create this structure
{"myTuple":(4,5,6)}

mySom = som.Som({'myTuple':(1,2,3)})
mySom.merge('myTuple',(4,5,6))
# It will automatically create this structure
{"myTuple":(1,2,3,4,5,6)}

```


### to_dict
Return the data hosted in the Som instance as a deep copy dictionary.\
Arguments:
* jsonCompatible : OPTIONAL : In case your dictionary has set, you would not be able to export it to JSON.
  This capability offer natively to transform the Som dictionary into one compatible with JSON. Transforming `set` to `list`.


### to_dataframe
Return the data as flatten dataframe
Arguments:
* expand_arrays : OPTIONAL : Default `False`, if set to `True`, it will create multiple rows for the arrays elements.

#### DataFrame Deepdive

by default the Som `to_dataframe` method will flatten all of the elements in the Som into a single row.\
It means that even list of object contains in your data will be flatten in a single row.\

Example of data:

```py
{"data":
  {
    "myfield":"value",
    "myList" : [1,2,3],
    "arrayObject1":[
      {
        "field_name":"array_item1",
        "arrayObject2":[
          {
            "field_name":"array_item_1_1"
          },
          {
            "field_name":"array_item_1_2"
          }
        ]
      },
      {
        "field_name":"array_item2"
      }
    ]
  }
}

```

The `to_dataframe` operation will return this type of table:

| data.myfield | data.mylist | data.arrayOfObject[0].field_name | data.arrayOfObject[0].arrayObject2[0].field_name | data.arrayOfObject[0].arrayObject2[1].field_name  | data.arrayOfObject[1].field_name |
| -- | --  | -- | -- | -- | -- |
| value | [1,2,3] | array_item1 | array_item_1_1 | array_item_1_2 |array_item2 |


If you set the `expand_arrays` array parameter to `True`, you will automatically create new rows for each element of the array of objects.\
The result of operation will return this type of table:

| data.myfield | data.mylist | data.arrayOfObject | data.arrayOfObject.field_name | data.arrayOfObject.arrayObject2 | data.arrayOfObject.arrayObject2.field_name |
| -- | --  | -- | -- | -- | -- |
| value | [1,2,3] | 0 | array_item1 | 0 | array_item_1_1 | 
| value | [1,2,3] | 0 | array_item1 | 1 | array_item_1_2 | 
| value | [1,2,3] | 1 | array_item2 | NaN | NaN |

### from_dataframe
Build a Som object from a **SINGLE** dataframe row or column.\
It only works when the data has been completely flatten (without `expand_arrays` set to `True`)\
The naming convention for element of arrays needs to be respected, ex: `[0]`
Arguments:
* dataFrame : REQUIRED : The dataframe countaining your data
* orient : OPTIONAL : The orientation of the dataframe. Default 0 by row. 1 by columns.
