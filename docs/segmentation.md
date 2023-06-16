# Segmentation module in aepp

This documentation will provide you some explanation on how to use the segmentation module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/segmentation/).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `segmentation` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import segmentation
```

The segmentation module provides a class that you can use for managing your segments.\
The following documentation will provide you with more information on its capabilities.

## The Segmentation class

The Segmentation class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `Segmentation()` from the `segmentation` module.

Following the previous method described above, you can realize this:

```python
mySegs = segmentation.Segmentation()
```

2 parameters are possible for the instantiation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

## Segmentation use-cases

The same way than for Query Service, most of the Segmentation capabilities can be achieved through the UI.\
However, if you really want to take advantage of this feature and develop it at scale, you need to create some sort of engine to run it on the cloud, and on demand.\
We will see the different use-cases focusing on using the most of the engine.

**IMPORTANT NOTE** : The segments definition that have been created by the API cannot be updated through the UI (2021 status).

### List all of your segments & their definitions

This may be the most basic use-case but it may not have always been easy to get all of the different that has been set in your organization through the UI.\
The API makes it available to retrieve that information and also transform that into a dataframe to work with the different elements.
You can also imagine updating the definition if needed.

In order to retrieve that information, you can use the `getSegments()` method as the following.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import segmentation
mySegs = segmentation.Segmentation()

mySegments = mySegs.getSegments()
```

### List all of your Real-Time Segments

As described in the documentation, not all of the segments are evaluated in real time [see detail here](https://experienceleague.adobe.com/docs/experience-platform/segmentation/api/streaming-segmentation.html?lang=en#retrieve-all-segments-enabled-for-streaming-segmentation).

With a parameter, you can identify the real-time segments.\
Following the last example:

```python
rltSegments = mySegs.getSegments(onlyRealTime=True)
```

### Get Preview

At some point in time, you may want to test some condition to see if they are actually qualifying users in your unified profile.\
You can realize a preview that will give you an estimate without actually creating the segment.

For that you would need to run 2 methods from the modules:

`createPreview` : This method will take the PQL statement (and optionally the schema class) to actually create a segment preview.

and

`getEstimate`: This method will return statistical information about the PQL statement that you have entered, by passing the previewId returned from the createPreview.

Another way to realize that is to use the `estimateExpression` that is available through that API.\
This method takes the 2 previous methods previously presented and linked them together.\
It takes the the PQL statement and optionally the schema class.

### Segments Jobs

Once you have defined the segments, you will need to run the segment to actually qualify the users within this segments.\
You can realize that by calling the `createJob()` method.

This method takes a list of segment ID and create a job for them.

```python
mySegs.createJob(['mySegmentId1','mySegmentId2'])
```

Therefore, if your segment is realized by Batch you can push a job without connecting within the UI.

### Segment Export

You can export Segments population to a dataSet by the usage of `exportJobs` method.\
The method takes a dictionary with the information to export.\
For more information on the dictionary to provide, reference the [documentation](https://experienceleague.adobe.com/docs/experience-platform/segmentation/api/export-jobs.html?lang=en#get)

The cool thing is that you can export all attributes of your profile for that segment population and you can change the mergeRuleId used for that segment.

### Create Schedule Jobs or Exports

You can automate segment job(s) and segment export(s) by using the `createSchedule` method.\
The dictionary to pass in order to create a schedule has a template accessible directly through this API as an instance attribute.\

```python
## get the template
mytemplate = mySegs.SCHEDULE_TEMPLATE
```
