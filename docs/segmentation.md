# Segmentation module in aepp

This documentation will provide you some explanation on how to use the segmentation module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/segmentation/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu
- [Segmentation module in aepp](#segmentation-module-in-aepp)
  - [Menu](#menu)
  - [What is the segmentation capability in AEP](#what-is-the-segmentation-capability-in-aep)
  - [Importing the module](#importing-the-module)
  - [The Segmentation class](#the-segmentation-class)
    - [Using kwargs](#using-kwargs)
  - [Segmentation attributes](#segmentation-attributes)
  - [Segmentation methods](#segmentation-methods)
  - [Segmentation use-cases](#segmentation-use-cases)
    - [1. List all of your segments and their definitions](#list-all-of-your-segments-and-their-definitions)
    - [2. List all of your Real-Time Segments](#list-all-of-your-real-time-segments)
    - [3. Get Preview](#get-preview)
    - [4. Create Segments Jobs](#create-segments-jobs)
    - [5. Segment Export](#segment-export)
    - [6. Create Schedule Jobs](#create-schedule-jobs)

## What is the segmentation capability in AEP

The segmentation capability allows you to create audiences through segment definitions or other sources from your Real-Time Customer Profile data.\
The audiences are always created based on Profile data in the AEP environment. It means that datasets not enabled for Profile (with schema also enabled for profile) are not contributed to the audience population.\
The segmentation capability will generate audiences based on 2 possibles elements:

* Audience Composition : Using existing segment definition, you can refine, enrich or split them based on certain [capabilities](https://experienceleague.adobe.com/en/docs/experience-platform/segmentation/ui/audience-composition).
* Segment Defintion : Using the PQL language, through UI or API, will provide a way to create conditions to match for the users in order to qualify for the segment.

Segments can then be activated to destinations (RTCDP, Adobe Solution) or read through via other services (AJO, QS).\

3 main type of evaluations can be done for segments:
* Batch segmentation : Daily run of condition match based on the computed snapshot of the profile data. (nightly run)
* Streaming segmentation : It is an ongoing data selection process that updates your audiences in response to user activity. Once an audience has been built and saved, the segment definition is applied against incoming data to Real-Time Customer Profile. 
* Edge segmentation : Edge segmentation is the ability to evaluate segments in Platform instantaneously on the Edge Network, enabling same-page and next-page personalization use cases. Mostly used for Target/AEP Web SDK capabilities.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `segmentation` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')

from aepp import segmentation
```

The segmentation module provides a class that you can use for managing your segments.\
The following documentation will provide you with more information on its capabilities.

## The Segmentation class

The Segmentation class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `Segmentation()` from the `segmentation` module.

Following the previous method described above, you can realize this:

```python
import aepp
from aepp import segmentation
prod = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='prod')
prodSegmentation = segmentation.Segmentation(config=prod)
```

3 parameters are possible for the instantiation of the class:

* config : OPTIONAL : the connect object instance created when you use `importConfigFile` with connectInstance parameter. Default to latest loaded configuration.
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : logging object to provide log of the application.

## Segmentation attributes

Once you have instantiated the `Segmentation` class, you have access to some attributes:

* sandbox : provide which sandbox is currently being used
* header : provide the default header which is used for the requests.
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods.
* SCHEDULE_TEMPLATE : a template to be used when you want to schedule segmentation jobs.
* PLATFORM_AUDIENCE_DICT : a template to be used to generate audience definition based on AEP data 
* EXTERNAL_AUDIENCE_DICT : a tempalte to be used for generate audience definition based on external audiences.


## Segmentation methods

### getSegments
Return segment definitions in your experience platfom instance.\
Arguments:
* onlyRealTime : OPTIONAL : If you wish to retrieve only real time compatible segment. (default False)\
Possible arguments:
* limit : number of segment returned per page

### getSegment
Return a specific segment definition.\
Argument:
* segment_id : REQUIRED : Segment ID of the segment to be retrieved.

### createSegment
Create a segment based on the information provided by the dictionary passed.\
Argument :
* segment_data : REQUIRED : Dictionary of the segment definition.\
    require in the segment_data: name, description, expression, schema, ttlInDays

### deleteSegment
Delete a specific segment definition.
Argument:
 * segment_id : REQUIRED : Segment ID of the segment to be deleted.

### updateSegment
Update the segment characteristics from the definition pass to that method.\
Arguments:
* segment_id : REQUIRED : id of the segment to be udpated.
* segment_data : REQUIRED : Dictionary of the segment definition.\
    require in the segment_data: name, description, expression, schema, ttlInDays\
possible kwargs:
* name : name of the segment to be udpated
* description : description of the segment to be udpated
* expression : expression of the segment to be udpated
* schema : schema of the segment to be udpated
* ttlInDay : ttlInDays to be updated

### getMultipleSegments
Retrieve multiple segments from a list of segment IDs.\
Arguments:
* segmentIds: REQUIRED : list of segment IDs


### convertSegmentDef
This endpoint converts a segment definition from pql/text to pql/json or from pql/json to pql/text.\
Arguments:
* name : REQUIRED : The name of the segment. It should be unique.
* expression : REQUIRED : the expriession regarding the transformation.
        A dictionary such as
        ```python
        {
            "type" : "PQL" (or "ARL"),
            "format" : "pql/text" (or "pql/json")
            "value" : "your PQL expression"
        }
        ```
* description : OPTIONAL : the description to be used
* schemaClass : OPTIONAL :  the class ID to be used. (ex: default : "_xdm.context.profile")
* ttl : OPTIONAL : Time to live per day (default 30)\
possible kwargs:
* additional kwargs will be used as parameter of the body

### getExportJobs
Retrieve a list of all export jobs.\
Arguments:
* limit : OPTIONAL : number of jobs to be returned (default 100)
* status : OPTIONAL : status of the job (NEW, SUCCEEDED, FAILED)

### createExport
Create an exportJob\
Arguments:
* export_request : REQUIRED : number of jobs to be returned (default 100)
* information on the structure of the request here: https://experienceleague.adobe.com/docs/experience-platform/segmentation/api/export-jobs.html?lang=en#get


### getExport
Retrieve a specific export Job.\
Arguments:
* export_id : REQUIRED : Export Job to be retrieved.

### deleteExport
Cancel or delete an export Job.\
Arguments:
* export_id : REQUIRED : Export Job to be deleted.

### searchNamespaces
Return a list of search count results, queried across all namespaces.\
Arguments:
* query : REQUIRED : the search query.
* schema : OPTIONAL : The schema class value associated with the search objects. (default _xdm.context.segmentdefinition)

### searchEntities
Return the list of objects that are contained  within a namespace.\
Arguments:
* query : REQUIRED : the search query based on Lucene query syntax (ex: name:test) (https://learn.microsoft.com/en-us/azure/search/query-lucene-syntax)
* schema : OPTIONAL : The schema class value associated with the search objects.(defaul _xdm.context.segmentdefinition)
* namespace : OPTIONAL : The namespace you want to search within (default ECID)
* entityId : OPTIONAL : The ID of the folder you want to search for external segments in
possible kwargs:
* limit : maximum number of result per page. Max 50.
* page : page to be retrieved (start at 0)
* page_limit : maximum number of pages retrieved.

### getSchedules
Return the list of scheduled segments.\
Arguments:
* limit : OPTIONAL : number of result per request (100 max)
* n_results : OPTIONAL : Total of number of result to retrieve.

### getSchedules
Return the list of scheduled segments.\
Arguments:
* limit : OPTIONAL : number of result per request (100 max)
* n_results : OPTIONAL : Total of number of result to retrieve.


### createSchedule
Schedule a segment to run.\
Arguments:
* schedule_data : REQUIRED : Definition of the schedule.
* Should contains name, type, properties, schedule.

### getSchedule
Get a specific schedule definition.\
Argument:
* scheduleId : REQUIRED : Segment ID to be retrieved.

### deleteSchedule
Delete a specific schedule definition.\
Argument:
* scheduleId : REQUIRED : Segment ID to be deleted.


### updateSchedule
Update a schedule with the operation provided.\
Arguments:
* scheduleId : REQUIRED : the schedule ID to update
* operations : REQUIRED : List of operations to realize
   ```python
        [
            {
            "op": "add",
            "path": "/state",
            "value": "active"
            }
        ]
    ```

### getJobs
Returns the list of segment jobs.\
Arguments:
* name : OPTIONAL : Name of the snapshot
* status : OPTIONAL : Status of the job (PROCESSING,SUCCEEDED)
* limit : OPTIONAL : Amount of jobs to be retrieved per request (100 max)
* n_results : OPTIONAL : How many total jobs do you want to retrieve.

### createJob
Create a new job for a segment.\
Argument:
* segmentIds : REQUIRED : a list of segmentIds.

### getJob
Retrieve a Segment job by ID.\
Argument:
* job_id: REQUIRED : The job ID to retrieve.

### deleteJob
deleteJob a Segment job by ID.\
Argument:
* job_id: REQUIRED : The job ID to delete.

### createPreview
Given a PQL expression genereate a preview of how much data there would be.\
Arguments:
* pql : REQUIRED : The PQL statement that would be your segment definition
* model : OPTIONAL : XDM class the statement is based on. Default : _xdm.context.profile

### getPreview
Retrieve the preview once it has been created by the createPreview method.\
Arguments:
* previewId : REQUIRED : The preview ID to used.

### deletePreview
Delete the preview based on its ID.\
Arguments:
* previewId : REQUIRED : The preview ID to deleted.

### getEstimate
Based on the preview ID generated by createPreview, you can look at statistical information of a segment.\
Arguments:
* previewId : REQUIRED : The preview ID to used for estimation

### estimateExpression
This method is a combination of the createPreview and getEstimate method so you don't have to build a pipeline for it.\
It automatically fetch the estimate based on the PQL statement passed. Run a loop every minute to fetch the result.\
Arguments:
* pql : REQUIRED : The PQL statement that would be your segment definition
* model : OPTIONAL : XDM class the statement is based on. Default : _xdm.context.profile
* wait : OPTIONAL : How many seconds to wait between 2 call to getEstimate when result are not ready. (default 60)

### getAudiences
Get the audiences list.\
Arguments:
* name : OPTIONAL : Filter audiences that contains that string in the name, case unsensitive.
* limit : OPTIONAL : The number of audiences to be returned by pages (default: 100)
* sort : OPTIONAL : If you want to sort by a specific attribute (ex: "updateTime:desc")
* prop : If you want to test a specific property of the result to filter the data.
            Ex: "audienceId==mytestAudienceId"
* description : OPTIONAL : Filter audiences that contains that string in the description, case unsensitive.

### getAudience
Retrieve a specific audience id.\
Arguments:
* audienceId : REQUIRED : The audience ID to retrieve.

### deleteAudience
Delete an audience based on its ID.
Argument:
* audienceId : REQUIRED : The audience ID to delete

### createAudience
Create an audience basde on the dictionary passed as argument.\
Argument:
* audienceObj : REQUIRED : Can be either one of the Platform Audience or External Audience\
    See constants EXTERNAL_AUDIENCE_DICT & PLATFORM_AUDIENCE_DICT

### patchAudience
PATCH an existing audience with some operation described in parameter.\
Arguments:
* audienceId : REQUIRED : The audience ID to patch
* operations : REQUIRED : A list of operation to apply.
    Example: 
    ```python
    [
        {
            "op": "add",
            "path": "/expression",
            "value": {
            "type": "PQL",
            "format": "pql/text",
            "value": "workAddress.country= \"US\""
            }
        }
    ]
    ``` 

### putAudience
Replace an existing definition with a new one, with the PUT method.\
Arguments:
* audienceId : REQUIRED : the audience ID to replace
* audienceObj : REQUIRED : the new definition to use\
   see EXTERNAL_AUDIENCE_DICT & PLATFORM_AUDIENCE_DICT

### extractPaths
**BETA**\
Extract the schema paths present in the segment or audience definition.\
Argument:
* audience : REQUIRED : Audience or segment definition.
* recursive : OPTIONAL : If you want to check the path used in the audience used in the audience

### extractAudiences
**BETA**\
Extract the audience Id used in the audience definition.\
In case you have build audience of audience.\
Argument: 
* audience : REQUIRED : Audience or Segment definition

## Segmentation use-cases

The same way than for Query Service, most of the Segmentation capabilities can be achieved through the UI.\
However, if you really want to take advantage of this feature and develop it at scale, you need to create some sort of engine to run it on the cloud, and on demand.\
We will see the different use-cases focusing on using the most of the engine.

**IMPORTANT NOTE** : The segments definition that have been created by the API cannot be updated through the UI (2021 status).

### List all of your segments and their definitions

This may be the most basic use-case but it may not have always been easy to get all of the different that has been set in your organization through the UI.\
The API makes it available to retrieve that information and also transform that into a dataframe to work with the different elements.
You can also imagine updating the definition if needed.

In order to retrieve that information, you can use the `getSegments()` method as the following.

```python
import aepp
dev = aepp.importConfigFile('myConfig_file.json',connectInstance=True,sandbox='dev')

from aepp import segmentation
devSegs = segmentation.Segmentation(config=dev)

mySegments = devSegs.getSegments()
```

### List all of your Real-Time Segments

As described in the documentation, not all of the segments are evaluated in real time [see detail here](https://experienceleague.adobe.com/docs/experience-platform/segmentation/api/streaming-segmentation.html?lang=en#retrieve-all-segments-enabled-for-streaming-segmentation).

With a parameter, you can identify the real-time segments.\
Following the last example:

```python
rltSegments = devSegs.getSegments(onlyRealTime=True)
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

### Create Segments Jobs

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

### Create Schedule Jobs

You can automate segment job(s) and segment export(s) by using the `createSchedule` method.\
The dictionary to pass in order to create a schedule has a template accessible directly through this API as an instance attribute.\

```python
## get the template
mytemplate = mySegs.SCHEDULE_TEMPLATE
```
