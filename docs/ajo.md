# AJO module in aepp

This documentation will provide you some explanation on how to use the AJO module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the Adobe Journey Optimizer API, please refer to this [API documentation](https://developer.adobe.com/journey-optimizer-apis/).\
Alternatively, you can use the docstring in the methods to have more information.

## Menu

- [AJO module in aepp](#ajo-module-in-aepp)
  - [Menu](#menu)
  - [What is the AJO module](#what-is-the-ajo-module)
  - [Importing the module](#importing-the-module)
  - [The AJO class](#the-ajo-class)
  - [AJO attributes](#ajo-attributes)
  - [AJO methods](#ajo-methods)
    - [Journeys](#journeys)
      - [getJourneys](#getjourneys)
      - [getJourney](#getjourney)
    - [Endpoint Capping](#endpoint-capping)
      - [getCappings](#getcappings)
      - [getCapping](#getcapping)
      - [createCapping](#createcapping)
      - [updateCapping](#updatecapping)
      - [deleteCapping](#deletecapping)
      - [deployCapping](#deploycapping)
      - [undeployCapping](#undeploycapping)
    - [Endpoint Throttling](#endpoint-throttling)
      - [getThrottlings](#getthrottlings)
      - [getThrottling](#getthrottling)
      - [createThrottling](#createthrottling)
      - [updateThrottling](#updatethrottling)
      - [deleteThrottling](#deletethrottling)
      - [checkThrottling](#checkthrottling)
      - [deployThrottling](#deploythrottling)
      - [undeployThrottling](#undeploythrottling)
    - [Surfaces](#surfaces)
      - [getSurfaces](#getsurfaces)
      - [getSurfaceDetail](#getsurfacedetail)
    - [Workflows](#workflows)
      - [getWorkflow](#getworkflow)
    - [Campaigns](#campaigns)
      - [getCampaigns](#getcampaigns)
      - [getCampaignVersions](#getcampaignversions)
      - [getCampaignDetails](#getcampaigndetails)
      - [getCampaignMessage](#getcampaignmessage)
      - [getCampaignMessageVariant](#getcampaignmessagevariant)
      - [getCampaignPublishingValidation](#getcampaignpublishingvalidation)
      - [getCampaignPackageDetails](#getcampaignpackagedetails)
    - [Message Execution](#message-execution)
      - [getMessageExecutionStatus](#getmessageexecutionstatus)
      - [getScheduleExecutionStatus](#getscheduleexecutionstatus)
      - [deleteScheduleExecution](#deletescheduleexecution)
      - [triggerUnitaryMessageExecution](#triggerunitarymessageexecution)
      - [triggerAudienceMessageExecution](#triggeraudiencemessageexecution)
      - [triggerUnitaryHighThrouputMessage](#triggerunitaryhighthrouputmessage)
      - [getUnitaryServiceHealth](#getunitaryservicehealth)
    - [Simulations](#simulations)
      - [triggerCampaignProofJob](#triggercampaignproofjob)
      - [getCampaignProofStatus](#getcampaignproofstatus)
      - [createCampaignPreview](#createcampaignpreview)
    - [Orchestrated Campaigns](#orchestrated-campaigns)
      - [validateDatasetOrchestration](#validatedatasetorchestration)
      - [getDatasetExtensionJob](#getdatasetextensionjob)
      - [enableDatasetOrchestration](#enabledatasetorchestration)
      - [triggerOrchestratedCampaign](#triggerorchestratedcampaign)
    - [Content Templates](#content-templates)
      - [getContentTemplates](#getcontenttemplates)
      - [getContentTemplate](#getcontenttemplate)
      - [createContentTemplate](#createcontenttemplate)
      - [putContentTemplate](#putcontenttemplate)
      - [patchContentTemplate](#patchcontenttemplate)
      - [deleteContentTemplate](#deletecontenttemplate)
    - [Content Fragments](#content-fragments)
      - [getContentFragments](#getcontentfragments)
      - [getContentFragment](#getcontentfragment)
      - [createContentFragment](#createcontentfragment)
      - [publishContentFragment](#publishcontentfragment)
      - [putContentFragment](#putcontentfragment)
      - [patchContentFragment](#patchcontentfragment)
      - [getContentFragmentLastPublication](#getcontentfragmentlastpublication)
      - [getContentFragmentPublicationStatus](#getcontentfragmentpublicationstatus)
    - [Suppression - Emails](#suppression---emails)
      - [getEmailsStatus](#getemailsstatus)
      - [getEmailStatus](#getemailstatus)
      - [createEmailsStatus](#createemailsstatus)
      - [deleteEmailStatus](#deleteemailstatus)
    - [Suppression - Domains](#suppression---domains)
      - [getDomainsStatus](#getdomainsstatus)
      - [getDomainStatus](#getdomainstatus)
      - [createDomainsStatus](#createdomainsstatus)
      - [deleteDomainStatus](#deletedomainstatus)
    - [Suppression - Upload Jobs](#suppression---upload-jobs)
      - [getUploadJobs](#getuploadjobs)
      - [getUploadJob](#getuploadjob)
      - [deleteUploadJob](#deleteuploadjob)
      - [deleteAllSuppressionData](#deleteallsuppressiondata)
      - [uploadSuppressionData](#uploadsuppressiondata)

## What is the AJO module

Adobe Journey Optimizer (AJO) is an application built on top of Adobe Experience Platform that allows companies to orchestrate and deliver connected, contextual, and personalized customer experiences across channels including email, push notifications, in-app messages, SMS, and more.\
The AJO module in `aepp` provides access to multiple AJO API capabilities, including:

- **Journeys**: Retrieve and manage journey definitions.
- **Capping & Throttling**: Configure rate limits on external endpoints used in actions and data sources.
- **Campaigns**: Manage campaign definitions, versions, messages, and publishing.
- **Message Execution**: Trigger unitary and audience-based message executions, including scheduled and high-throughput scenarios.
- **Simulations**: Validate campaigns through proof jobs and previews before going live.
- **Orchestrated Campaigns**: Manage dataset extensions and trigger orchestrated campaign flows.
- **Content Templates & Fragments**: Create, update, and manage reusable content assets.
- **Suppression Management**: Manage email and domain suppression and allow lists.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [See getting started](./getting-started.md)

To import the module you can use the import statement with the `ajo` keyword.

```python
import aepp
prod = aepp.importConfigFile('myConfig_file.json', connectInstance=True, sandbox='prod')

from aepp import ajo
```

The AJO module provides a class that you can use for managing your AJO configurations and executions.\
The following documentation will provide you with more information on its capabilities.

## The AJO class

The AJO class uses the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `AJO()` from the `ajo` module.

Following the previous method described above, you can realize this:

```python
import aepp
from aepp import ajo
prod = aepp.importConfigFile('myConfig_file.json', connectInstance=True, sandbox='prod')
myAjo = ajo.AJO(config=prod)
```

3 parameters are possible for the instantiation of the class:

* config : OPTIONAL : the connect object instance created when you use `importConfigFile` with the `connectInstance` parameter. Default to latest loaded configuration.
* header : OPTIONAL : header object in the config module. (example: `aepp.config.header`)
* loggingObject : OPTIONAL : logging object to provide log of the application. See [logging documentation](./logging.md).

## AJO attributes

Once you have instantiated the `AJO` class, you have access to some attributes:

* sandbox : provides which sandbox is currently being used
* header : provides the default header which is used for the requests
* loggingEnabled : if the logging capability has been used
* endpoint : the default endpoint used for all methods

## AJO methods

### Journeys

#### getJourneys

Returns a list of journeys based on the provided filters. If no filters are used, retrieves all the journeys in the sandbox.\
Arguments:
* filter : OPTIONAL : Search filters in URL-encoded format. Supports `&`-separated fields with basic operators `=`, `>`, `<`, `>=`, `<=`. Example: `status=draft,live&metadata.lastModifiedAt>2024-12-25`
* fields : OPTIONAL : Comma-separated list of fields to include in the response. Example: `name,status,metadata,createdBy`
* sort : OPTIONAL : Sort criteria in format `field=direction`. Direction can be `asc` or `desc`. Example: `name=asc,metadata.createdAt=desc`

#### getJourney

Returns the details of a specific journey.\
Arguments:
* journeyId : REQUIRED : The unique identifier of the journey to retrieve.
* include : OPTIONAL : Comma-separated list of additional data to include in the response (e.g., `"campaigns,surfaces,rulesets"`).

---

### Endpoint Capping

Endpoint capping allows you to limit the number of calls sent to an external system used in AJO actions or data sources.

#### getCappings

Returns the list of all endpoint capping configurations defined for the given IMS organization and sandbox.\
No arguments required.

#### getCapping

Returns the endpoint capping configuration for a specific endpoint.\
Arguments:
* uid : REQUIRED : The unique identifier of the endpoint capping configuration to retrieve.

#### createCapping

Creates a capping configuration on a given endpoint identified by its URL.\
Arguments:
* data : OPTIONAL : The full endpoint capping configuration as a dictionary. If provided, `url` and `methods` keys are required inside it.
* url : OPTIONAL : The URL of the endpoint to cap (e.g., `"https://api.example.org/data/2.5/weather"`). Required if `data` is not provided.
* methods : OPTIONAL : The methods called on this endpoint, as defined in the actions or data sources. Example: `["GET", "POST"]`
* action : OPTIONAL : Indicates if the capping will be applied when executing a Custom Action.
* maxHttpConnections : OPTIONAL : Max count of simultaneous connections to the endpoint (max 400).
* maxCallsCount : OPTIONAL : Max count of calls to the endpoint in the defined period.
* periodInMs : OPTIONAL : The period for the `maxCallsCount` limitation, in milliseconds (must be greater than 0).

#### updateCapping

Updates an existing capping configuration. Takes the same arguments as `createCapping` plus:
* uid : REQUIRED : The unique identifier of the endpoint capping configuration to update.

#### deleteCapping

Deletes an endpoint capping configuration. The configuration must be undeployed before deletion.\
Arguments:
* uid : REQUIRED : The unique identifier of the endpoint capping configuration to delete.

#### deployCapping

Deploys an endpoint capping configuration.\
Arguments:
* uid : REQUIRED : The unique identifier of the endpoint capping configuration to deploy.

#### undeployCapping

Undeploys an endpoint capping configuration.\
Arguments:
* uid : REQUIRED : The unique identifier of the endpoint capping configuration to undeploy.

---

### Endpoint Throttling

Endpoint throttling allows you to limit the throughput (calls per second) on an external endpoint used in AJO actions.

#### getThrottlings

Returns the list of all endpoint throttling configurations defined for the given IMS organization and sandbox.\
No arguments required.

#### getThrottling

Returns a specific endpoint throttling configuration.\
Arguments:
* uid : REQUIRED : The unique identifier of the endpoint throttling configuration to retrieve.

#### createThrottling

Creates a new endpoint throttling configuration.\
Arguments:
* data : OPTIONAL : The full throttling configuration as a dictionary. If provided, `urlPattern`, `methods`, and `maxThroughput` keys are required inside it.
* name : OPTIONAL : The name of the throttling configuration. Required if `data` is not provided.
* description : OPTIONAL : The description of the throttling configuration. Default is an empty string.
* urlPattern : OPTIONAL : The URL pattern of the endpoint to throttle (e.g., `"https://api.example.org/data/2.5/*"`). Required if `data` is not provided.
* methods : OPTIONAL : The methods to throttle on this endpoint. Example: `["POST", "PUT"]`
* maxThroughput : OPTIONAL : The maximum throughput for the endpoint, in calls per second. Required if `data` is not provided.

#### updateThrottling

Updates an existing throttling configuration. Takes the same arguments as `createThrottling` plus:
* uid : REQUIRED : The unique identifier of the endpoint throttling configuration to update.

#### deleteThrottling

Deletes an endpoint throttling configuration.\
Arguments:
* uid : REQUIRED : The unique identifier of the endpoint throttling configuration to delete.

#### checkThrottling

Checks if a throttling configuration can be deployed.\
Arguments:
* uid : REQUIRED : The unique identifier of the endpoint throttling configuration to check.

#### deployThrottling

Deploys an endpoint throttling configuration.\
Arguments:
* uid : REQUIRED : The unique identifier of the endpoint throttling configuration to deploy.

#### undeployThrottling

Undeploys an endpoint throttling configuration.\
Arguments:
* uid : REQUIRED : The unique identifier of the endpoint throttling configuration to undeploy.

---

### Surfaces

A surface represents a channel-specific configuration (e.g., in-app, push, email) used by campaigns.

#### getSurfaces

Returns the list of all surfaces defined for the given IMS organization and sandbox.\
Arguments:
* count : OPTIONAL : The maximum number of surfaces to return. Default: `50`.
* orderBy : OPTIONAL : The field to order the surfaces by. Default: `"surfaceName"`.
* channel : OPTIONAL : The channel of the surfaces to return. Default: `"inapp"`.
* prop : OPTIONAL : A property filter (e.g., `"surfaceName==ajo;created_at>2021-09-28"`).
* surfaceType : OPTIONAL : The type of surface to filter on. One of: `"appConfigurationId"`, `"channelConfigurationId"`, `"surfaceId"`, `"brandingPresetId"`.

#### getSurfaceDetail

Returns the details of a specific surface.\
Arguments:
* channel : REQUIRED : The channel of the surface to return.
* surfaceId : REQUIRED : The unique identifier of the surface to return.

---

### Workflows

#### getWorkflow

Returns the details of a campaign workflow.\
Arguments:
* workflowId : REQUIRED : The unique identifier of the workflow to return.

---

### Campaigns

#### getCampaigns

Returns the list of all campaigns defined for the given IMS organization and sandbox.\
Arguments:
* prop : OPTIONAL : A property filter (e.g., `"campaignClass!=inline;name=like=my campaign name"`).
* full : OPTIONAL : Whether to return full campaign details or only the summary. Default: `False`.
* actions : OPTIONAL : Whether to include actions associated with the campaigns. Default: `True`.
* orderBy : OPTIONAL : The field by which to order the campaigns. Default: `"name"`.

#### getCampaignVersions

Returns the list of all versions for a given campaign.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign.
* prop : OPTIONAL : A property filter.
* full : OPTIONAL : Whether to return full details. Default: `False`.
* actions : OPTIONAL : Whether to include actions. Default: `True`.

#### getCampaignDetails

Returns the full details of a specific campaign.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign.

#### getCampaignMessage

Returns the details of a specific message within a campaign.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign.
* messageId : REQUIRED : The unique identifier of the message.

#### getCampaignMessageVariant

Returns the details of a message variant for a specific channel within a campaign.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign.
* messageId : REQUIRED : The unique identifier of the message.
* channel : REQUIRED : The channel of the message (e.g., `"email"`, `"push"`).
* variantId : REQUIRED : The unique identifier of the variant.

#### getCampaignPublishingValidation

Returns the publishing validation result for a campaign.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign.
* orderBy : OPTIONAL : The field by which to order the validation results.
* prop : OPTIONAL : A property filter (e.g., `"status==error"`).

#### getCampaignPackageDetails

Returns the details of a specific package within a campaign.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign.
* packageId : REQUIRED : The unique identifier of the package.

---

### Message Execution

#### getMessageExecutionStatus

Returns the execution status of a message.\
Arguments:
* executionId : REQUIRED : The unique identifier of the message execution.

#### getScheduleExecutionStatus

Returns the execution status of a scheduled execution.\
Arguments:
* scheduleId : REQUIRED : The unique identifier of the scheduled execution.

#### deleteScheduleExecution

Deletes a scheduled execution.\
Arguments:
* scheduleId : REQUIRED : The unique identifier of the scheduled execution to delete.

#### triggerUnitaryMessageExecution

Triggers the execution of a unitary (one-to-one) message for a list of recipients.\
Arguments:
* data : OPTIONAL : The full payload as a dictionary. Requires `requestId`, `campaignId`, and `recipients` keys.
* requestId : REQUIRED : A unique identifier for this execution request.
* campaignId : REQUIRED : The campaign to execute.
* recipients : REQUIRED : A list of recipient dictionaries. Each recipient example:

```python
{
    "type": "aep",
    "userId": "AEP-ProfileID-12345",
    "namespace": "email",
    "mergePolicyName": "Default Timebased",
    "mergePolicySchema": "_xdm.context.profile",
    "channelData": {
        "emailAddress": "customer@example.com",
        "mobilePhoneNumber": "111-111-1111"
    },
    "profile": {
        "person": {
            "name": {
                "firstName": "Jane",
                "lastName": "Doe"
            }
        }
    },
    "context": {
        "product": "Gaming Laptop"
    }
}
```

#### triggerAudienceMessageExecution

Triggers a message execution for an entire audience. Can also be scheduled.\
Arguments:
* data : OPTIONAL : The full payload as a dictionary. Requires `requestId`, `campaignId`, `audienceId`, and `schedule` keys.
* requestId : REQUIRED : A unique identifier for this execution request.
* campaignId : REQUIRED : The campaign to execute.
* audienceId : REQUIRED : The audience segment to target.
* context : OPTIONAL : Additional context information as a dictionary (e.g., product details, event info).
* schedule : REQUIRED : The ISO 8601 scheduled execution time. Example: `"2016-08-29T09:12:33.001Z"`

#### triggerUnitaryHighThrouputMessage

Triggers a unitary message execution optimized for high-volume scenarios. Does not return execution status in real time.\
Arguments:
* data : OPTIONAL : The full payload as a dictionary. Requires `requestId`, `campaignId`, and `recipients` keys.
* requestId : REQUIRED : A unique identifier for this execution request.
* campaignId : REQUIRED : The campaign to execute.
* recipients : REQUIRED : A list of recipient dictionaries. Each recipient example:

```python
{
    "type": "external",
    "userId": "customer@example.com",
    "namespace": "email",
    "channelData": {
        "emailAddress": "customer@example.com",
        "mobilePhoneNumber": "111-111-1111"
    },
    "profile": {
        "person": {
            "name": {
                "firstName": "Jane",
                "lastName": "Doe"
            }
        }
    },
    "context": {
        "product": "Gaming Laptop"
    }
}
```

#### getUnitaryServiceHealth

Returns the health status of the unitary message execution service.\
No arguments required.

---

### Simulations

Simulations allow you to validate campaign content and configuration before going live, using proof jobs and previews.

#### triggerCampaignProofJob

Triggers a proof job for a campaign. A proof job sends the campaign to a list of test recipients to validate content and configuration.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign.
* recipients : REQUIRED : A list of recipient dictionaries. Each recipient example:

```python
{
    "userId": "test@gmail.com",
    "namespace": "Email",
    "channelsData": [
        {
            "channel": "email",
            "subjectPrefix": "TEST - ",
            "emailAddresses": []
        }
    ],
    "profile": {},
    "context": {}
}
```

#### getCampaignProofStatus

Returns the status of a campaign proof job.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign.
* proofId : REQUIRED : The unique identifier of the proof job.

#### createCampaignPreview

Creates a preview for a campaign. A preview simulates the execution without sending messages and returns the expected rendered content.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign.
* previewRequestItems : REQUIRED : A list of preview request item dictionaries. Each item requires `userId` and `namespace` fields. Example:

```python
{
    "userId": "test@gmail.com",
    "namespace": "Email",
    "profileAttributes": {},
    "contextAttributes": {}
}
```

---

### Orchestrated Campaigns

Orchestrated campaigns allow multi-step customer journeys driven by relational datasets with CDC (Change Data Capture) support.

#### validateDatasetOrchestration

Validates whether the Orchestrated Campaign extension can be applied on a dataset. The dataset must meet the following criteria:
- Associated with a model-based schema
- Not a System dataset or Profile-enabled dataset
- Schema behavior set to `record` (timeseries is not supported)
- Schema defines both a primary key and a version descriptor
- Dataset must be of CDC type
- Orchestrated Campaign extension not already enabled or in progress

Arguments:
* datasetId : REQUIRED : The unique identifier of the dataset to validate.

#### getDatasetExtensionJob

Returns the details of a dataset extension enablement job.\
Arguments:
* jobId : REQUIRED : The job ID of the dataset enablement request.

#### enableDatasetOrchestration

Enables the Orchestrated Campaign extension on one or more validated datasets. Triggers an asynchronous dataset extension job.\
Arguments:
* datasetIds : REQUIRED : A list of dataset IDs to enable.

#### triggerOrchestratedCampaign

Triggers the execution of an orchestrated campaign that is in `DRAFT` status.\
Arguments:
* campaignId : REQUIRED : The unique identifier of the campaign to trigger.

---

### Content Templates

Content templates are reusable content definitions that can be referenced across orchestrated campaigns.

#### getContentTemplates

Returns the list of all content templates for the given IMS organization and sandbox.\
Arguments:
* prop : OPTIONAL : A property filter (e.g., `"templateName==myTemplate"`).
* orderBy : OPTIONAL : The field to order results by (e.g., `"modifiedAt"`).

#### getContentTemplate

Returns the details of a specific content template.\
Arguments:
* templateId : REQUIRED : Content Template ID.

#### createContentTemplate

Creates a new content template.\
Arguments:
* data : REQUIRED : The full content template payload as a dictionary. Example:

```python
{
    "name": "Cyber Monday Sale - Header",
    "description": "Cyber Monday Sale Header Banner",
    "templateType": "html",
    "channels": ["email"],
    "source": {
        "origin": "ajo",
        "metadata": {}
    },
    "subType": "HTML",
    "template": {
        "html": "<html> Hi {{profile.person.name}} </html>",
        "editorContext": {}
    }
}
```

#### putContentTemplate

Fully replaces an existing content template.\
Arguments:
* templateId : REQUIRED : Content Template ID.
* data : REQUIRED : The full content template payload as a dictionary (same structure as `createContentTemplate`).

#### patchContentTemplate

Partially updates an existing content template using JSON Patch operations.\
Arguments:
* templateId : REQUIRED : Content Template ID.
* data : REQUIRED : A list of patch operation dictionaries. Example:

```python
[
    {
        "op": "add",
        "path": "/description",
        "value": "Updated description"
    }
]
```

#### deleteContentTemplate

Deletes a content template.\
Arguments:
* templateId : REQUIRED : Content Template ID.

---

### Content Fragments

Content fragments are reusable pieces of content (e.g., HTML blocks) that can be referenced inside content templates.

#### getContentFragments

Returns the list of all content fragments for the given IMS organization and sandbox.\
Arguments:
* prop : OPTIONAL : A property filter (e.g., `"fragmentName==myFragment"`).
* orderBy : OPTIONAL : The field to order results by (e.g., `"modifiedAt"`).

#### getContentFragment

Returns the details of a specific content fragment.\
Arguments:
* fragmentId : REQUIRED : Content Fragment ID.

#### createContentFragment

Creates a new content fragment. The `name`, `type`, `fragment`, and `channels` fields are required in the payload.\
Arguments:
* data : REQUIRED : The full content fragment payload as a dictionary. Example:

```python
{
    "name": "Promo Banner",
    "description": "Promotional Banner Fragment",
    "type": "html",
    "source": {
        "origin": "ajo",
        "metadata": {}
    },
    "fragment": {
        "content": "<div> Hi {{profile.person.name}} </div>",
        "editorContext": {}
    },
    "channels": ["email"]
}
```

#### publishContentFragment

Publishes a content fragment, making it available for use in content templates.\
Arguments:
* fragmentId : REQUIRED : Content Fragment ID.

#### putContentFragment

Fully replaces an existing content fragment.\
Arguments:
* fragmentId : REQUIRED : Content Fragment ID.
* data : REQUIRED : The full content fragment payload as a dictionary (same structure as `createContentFragment`).

#### patchContentFragment

Partially updates a content fragment using JSON Patch operations.\
Arguments:
* fragmentId : REQUIRED : Content Fragment ID.
* data : REQUIRED : A list of patch operation dictionaries. Example:

```python
[
    {
        "op": "add",
        "path": "/description",
        "value": "Updated description"
    }
]
```

#### getContentFragmentLastPublication

Returns the details of the last published version of a content fragment.\
Arguments:
* fragmentId : REQUIRED : Content Fragment ID.

#### getContentFragmentPublicationStatus

Fetches the status of the last publication request for a content fragment.\
A fragment can have multiple publications and the publication can be successful, in progress, or can error out.\
Arguments:
* fragmentId : REQUIRED : Content Fragment ID.

---

### Suppression - Emails

The suppression list controls which email addresses are blocked from receiving communications (`client`) or explicitly allowed (`allowed`).

#### getEmailsStatus

Returns the list of email addresses with a suppression or allow status.\
Arguments:
* statusType : REQUIRED : `"client"` for suppressed entities, `"allowed"` for allowed entities.
* prop : OPTIONAL : A property filter (e.g., `"creationdate<1631739725150"`).
* orderBy : OPTIONAL : The field to order results by (e.g., `"-creationdate"`).

#### getEmailStatus

Returns the suppression or allow status of a specific email address.\
Arguments:
* email : REQUIRED : The email address to check.
* statusType : REQUIRED : `"client"` for suppressed entities, `"allowed"` for allowed entities.

#### createEmailsStatus

Adds a list of email addresses to the suppression or allow list.\
Arguments:
* statusType : REQUIRED : `"client"` for suppressed entities, `"allowed"` for allowed entities.
* data : REQUIRED : A list of email entry dictionaries. Example:

```python
[
    {
        "entity": {
            "type": "email",
            "entityValue": "bademailaddress@domain.com"
        },
        "comment": "Known bad email address",
        "user": "admin@corp.com"
    }
]
```

#### deleteEmailStatus

Removes the suppression or allow status for a specific email address.\
Arguments:
* email : REQUIRED : The email address to remove from the list.
* statusType : REQUIRED : `"client"` for suppressed entities, `"allowed"` for allowed entities.

---

### Suppression - Domains

#### getDomainsStatus

Returns the list of domains with a suppression or allow status.\
Arguments:
* statusType : REQUIRED : `"client"` for suppressed entities, `"allowed"` for allowed entities.
* prop : OPTIONAL : A property filter (e.g., `"creationdate<1631739725150"`).
* orderBy : OPTIONAL : The field to order results by (e.g., `"-creationdate"`).

#### getDomainStatus

Returns the suppression or allow status of a specific domain.\
Arguments:
* domain : REQUIRED : The domain to check.
* statusType : REQUIRED : `"client"` for suppressed entities, `"allowed"` for allowed entities.

#### createDomainsStatus

Adds a list of domains to the suppression or allow list.\
Arguments:
* statusType : REQUIRED : `"client"` for suppressed entities, `"allowed"` for allowed entities.
* data : REQUIRED : A list of domain entry dictionaries. Example:

```python
[
    {
        "entity": {
            "type": "domain",
            "entityValue": "baddomain.com"
        },
        "comment": "Known bad domain",
        "user": "admin@corp.com"
    }
]
```

#### deleteDomainStatus

Removes the suppression or allow status for a specific domain.\
Arguments:
* domain : REQUIRED : The domain to remove from the list.
* statusType : REQUIRED : `"client"` for suppressed entities, `"allowed"` for allowed entities.

---

### Suppression - Upload Jobs

Upload jobs allow you to bulk-upload a CSV file of email addresses or domains to the suppression or allow list.

#### getUploadJobs

Returns the list of upload jobs for the sandbox.\
Arguments:
* prop : OPTIONAL : A property filter (e.g., `"creationdate<1631739725150"`).
* orderBy : OPTIONAL : The field to order results by (e.g., `"-creationdate"`).

#### getUploadJob

Returns the details of a specific upload job.\
Arguments:
* jobId : REQUIRED : The unique identifier of the upload job.

#### deleteUploadJob

Deletes a specific upload job.\
Arguments:
* jobId : REQUIRED : The unique identifier of the upload job.

#### deleteAllSuppressionData

Deletes all suppression data (emails and domains) for the current sandbox and AJO setup. This effectively clears the entire suppression list.\
No arguments required.

#### uploadSuppressionData

Uploads a CSV file to bulk-populate the suppression or allow list.\
The CSV file must contain a header and a column named `entityValue` with the email addresses or domains to suppress or allow.\
Arguments:
* statusType : REQUIRED : `"client"` for suppressed entities, `"allowed"` for allowed entities.
* filePath : REQUIRED : The local file path of the CSV file to upload.
