# Tags module in aepp

This documentation will provide you some explanation on how to use the tags module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the tags API, please refer to this API documentation. (to be published)\
Alternatively, you can use the docstring in the methods to have more information.\

## Menu

- [Tags module in aepp](#tags-module-in-aepp)
  - [Menu](#menu)
  - [Importing the module](#importing-the-module)
  - [The Tags class](#the-sandboxes-class)
  - [Tags attributes](#sandboxes-attributes)
  - [Tags methods](#sandboxes-methods)


## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `tags` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')

from aepp import tags
```

The tags module provides a class `Tags` that you can use for generating and retrieving tags.\
The following documentation will provide you with more information on its usage.

## The Tags class

The `Tags` class is generating a connection to use the different methods directly on your AEP sandbox / instance.\
This class can be instantiated by calling the `Tags()` from the `tags` module.

Following the previous method described above, you can realize this:

```python
import aepp
from aepp import tags

prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')
myTags = tags.Tags(config=prod)
```

3 parameters are possible for the instantiation of the class:

* config : OPTIONAL : the connect object instance created when you use `importConfigFile` with connectInstance parameter. Default to latest loaded configuration.
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : logging object to provide log of the application.

**Note**: Kwargs can be used to update the header used in the connection.

## Tags attributes

Once you have instantiated the `Tags` class, you have access to some attributes:

* sandbox : provide which sandbox is currently being used
* header : provide the default header which is used for the requests.
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods.

## Tags methods

The following elements are all the methods available once you have instantiated the `Tags` class.

### getCategories
Retrieve the categories of the tags.

### getCategory
Retrieve the tag category based on the ID passed.\
Arguments:
* tagCategoryId : REQUIRED : The Id of the tag category to retrieve


### createCategory
Create a tag category\
Arguments:
* name : REQUIRED : name of the category
* description : OPTIONAL : description of the category


### patchCategory
Patch the category with new definition\
Arguments:
* tagCategoryId : REQUIRED : The ID of the category to update
* operation : OPTIONAL : A dictionary that provides the operation to performed\
  ex: 
  ```python
    {
        "op": "replace",
        "path": "description",
        "value": "Updated sample description"
    }
  ```
* op : OPTIONAL : In case the individual value for "op" in the operation is provided. Possible value: "replace"
* path : OPTIONAL : In case the individual value for "path" in the operation is provided.
* value : OPTIONAL : In case the individual value for "value" in the operation is provided.

### deleteTagCategory
Delete the tag category based on its ID.\
Arguments:
* tagCategoryId : REQUIRED : Tag Category ID to be deleted

### getTags
Retrieve a list of tag based on the categoryId\
Arguments:
* tagCategoryId : OPTIONAL : The id of the category to get your tags

### getTag
Retrieve a specific tag based on its ID.\
Argument:
* tagId : REQUIRED : The tag ID to be used

### createTag
Create a new tag.\
Arguments:
* name : REQUIRED : Name of the tag
* tagCategoryId : OPTIONAL : The category ID of the tag


### patchTag
Update a specific Tag\
Arguments:
* tagId : REQUIRED : The tag Id to be updated
* operation : OPTIONAL : The full operation dictionary
  ex: 
  ```python
  {
        "op": "replace",
        "path": "description",
        "value": "Updated sample description"
    }
  ```
* op : OPTIONAL : In case the individual value for "op" in the operation is provided. default value: "replace"
* path : OPTIONAL : In case the individual value for "path" in the operation is provided.
* value : OPTIONAL : In case the individual value for "value" in the operation is provided.

### deleteTag
Delete a tag by its ID.\
Arguments:
* tagId : REQUIRED : The Tag Id to be deleted


### validateTags
Validate if specific tag Ids exist.\
Arguments: 
* tagsIds : REQUIRE : List of tag Ids to validate

### getFolders
Retrieve the folders for the tags.\
Arguments:
* folderType : REQUIRED : Default "segment", possible values: "dataset"

### getSubFolders
Return the list of subfolders.\
Arguments:
* folderType : REQUIRED : Default "segment", possible values: "dataset"
* folderId : REQUIRED : The folder ID that you want to retrieve

### getSubFolder
Return a specific sub folder\
Arguments:
* folderType : REQUIRED : Default "segment", possible values: "dataset"
* folderId : REQUIRED : The folder ID that you want to retrieve

### deleteSubFolder
Delete a specific subFolder\
Arguments:
* folderType : REQUIRED : Default "segment", possible values: "datasets"
* folderId : REQUIRED : The folder ID you want to delete

### createSubFolder
Create a sub Folder.\
Arguments:
* folderType : REQUIRED : Default "segment", possible values: "dataset"
* name : REQUIRED : Name of the folder
* parentId : REQUIRED : The parentID attached to your folder 

### updateFolder
Update an existing folder name\
Arguments:
* folderType : REQUIRED : Default "segment", possible values: "dataset"
* folderId : REQUIRED : the folder ID you want to rename
* name : OPTIONAL : The new name you want to give that folder
* parentFolderId : OPTIONAL : The new parent folder id 

### validateFolder
Validate if a folder is eligible to have objects in it\
Arguments:
* folderType : REQUIRED : Default "segment", possible values: "dataset"
* folderId : REQUIRED : The Folder ID

