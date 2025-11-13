# Destination Authoring module in aepp

This documentation will provide you some explanation on how to use the `destination` module and different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/destination-authoring/).\
Alternatively, you can use the docstring in the methods to have more information.

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `destination` keyword.

```python
import aepp
sandbox = aepp.importConfigFile('myConfig_file.json',sandbox='mysandbox', connectedInstance=True)

from aepp import destination
```

The destination module provides a class that you can use to generate a SDK taking care of transfering some information to specific destination endpoints.\
The following documentation will provide you with more information on its capabilities.

## The Authoring class

The Authoring class is the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `Authoring()` from the `destination` module.

Following the previous method described above, you can realize this:

```py
mySDK = destination.Authoring(config=sandbox)
```

3 parameters are possible for the instantiation of the class:

* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)
* loggingObject : OPTIONAL : logging object to provide log of the application.


## Destination module use-cases

The Destination module will enable you to generate a destination application in AEP.\
This application can then deliver aduience and profile data to the endpoint selected.\
The configuration of that application is stored in the Experience Platform. Note that you can also add some authentication methods to your application.

The destination API supports real-time integration with destinations that have a REST API endpoint.\
The capabilities supported are:
* Message transformation and aggregation
* Profile Backfill
* Configurable metadata integration to initialize audience setup and data transfer
* Configurable authentication
* A suite of testing & validation APIs for you to test and iterate your destination configurations

NOTE: You need to have acces to the Activation package to use this API.

The complete documentation of the destination Authoring API is available in the experience league: https://experienceleague.adobe.com/docs/experience-platform/destinations/destination-sdk/overview.html?lang=en

## Destination methods

This part is describing the different methods available from that module, once you have generated your instance.

* getDestinations
  Return a list of all destination SDK authored by the organization.

* getDestination
  Return a destination specific configuration.
  Arguments:
  * destinationId : REQUIRED : The destination ID to be retrieved

* deleteDestination
  Delete a specific destination based on its ID.
  Arguments:
  * destinationId : REQUIRED : The destination ID to be deleted

* createDestination
  Create a destination based on the definition passed in argument.
  Arguments:
  * destinationObj : REQUIRED : Object containing the definition of the destination.

* updateDestination
  Create a destination based on the definition passed in argument.
  Arguments:
  * destinationId : REQUIRED : The destination ID to be updated
  * destinationObj : REQUIRED : Object containing the definition of the destination.

* getDestinationServers
  Retrieve a list of all destination server configurations for your IMS Organization

* getDestinationServer
  Retrieve a specific destination server configuration by its ID.
  Arguments:
  * serverId : REQUIRED : destination server ID of the server

* deleteDestinationServer
  Delete a destination server by its ID.
  Arguments:
  * serverId : REQUIRED : destination server ID to be deleted

* createDestinationServer
  Create a new destination server configuration.
  Arguments:
  * serverObj : REQUIRED : dictionary containing the server destination configuration   

* updateDestinationServer
  Update the destination with a new definition (PUT request)
  Arguments:
  * serverId : REQUIRED : destination server ID to be updated
  * serverObj : REQUIRED : dictionary containing the server configuration

* getAudienceTemplates
  Return a list of all audience templates for your IMS Organization

* getAudienceTemplate
  Return a specific Audience Template.
  Arguments:
  * audienceId : REQUIRED : The ID of the audience template configuration that you want to retrieve.
        
* deleteAudienceTemplate
  Delete a specific Audience Template.
  Arguments:
  * audienceId : REQUIRED : The ID of the audience template configuration that you want to delete

* createAudienceTemplate
  Create a specific Audience Template based on a dictionary definition passed as parameter.
  Arguments:
  * templateObj : REQUIRED : The ID of the audience template configuration that you want to retrieve.

* updateAudienceTemplate
  Update a specific Audience Template based on a dictionary definition passed as parameter.
  Arguments:
  * audienceId : REQUIRED : The ID of the audience template configuration that you want to delete
  * templateObj : REQUIRED : The ID of the audience template configuration that you want to retrieve.

* getCredentials
  Retrieve a list of all credentials configurations for your IMS Organization 

* getCredential
  Return a specific credential based on its ID.
  Arguments:
  * credentialId : REQUIRED : The ID of the credential to retrieve

* deleteCredential
  Delete a specific credential based on its ID.
  Arguments:
  * credentialId : REQUIRED : The ID of the credential to delete

* createCredential
  Create a credential configuration based on the dictionary passed.
  Arguments:
  * credentialObj : REQUIRED : The credential object definition

* updateCredential
  Update the credential configuration based on the dictionary and the credential ID passed.
  Arguments:
  * credentialId : REQUIRED : The credentialId to be updated
  * credentialObj : REQUIRED : The credential object definition

* getSampleProfile
  Generate a sample profile of a destination given the correct arguments.
  Arguments:
  * destinationInstanceId : REQUIRED : Also known as order ID. The ID of the destination instance based on which you are generating sample profiles. (example: "49966037-32cd-4457-a105-2cbf9c01826a")
    Documentation on how to retrieve it: https://experienceleague.adobe.com/docs/experience-platform/destinations/destination-sdk/api/developer-tools-reference/destination-testing-api.html?lang=en#get-destination-instance-id
  * destinationId : REQUIRED : he ID of the destination configuration based on which you are generating sample profiles. The destination ID that you should use here is the ID that corresponds to a destination configuration, created using the createDestination method.
  * count : OPTIONAL : The number of sample profiles that you are generating. The parameter can take values between 1 - 1000.

* getSampleDestination
  Returns a sample template corresponding to the destinationID passed.
  Argument
  * destinationConfigId : REQUIRED : The ID of the destination configuration for which you are generating a message transformation template.
    The destination ID that you should use here is the ID that corresponds to a destination configuration, created using the createDestination method

* generateTestProfile
  Generate exported data by making a POST request to the testing/template/render endpoint and providing the destination ID of the destination configuration and the template you created using the sample template API endpoint
  Arguments:
  * destinationId : REQUIRED : The ID of the destination configuration for which you are rendering exported data.
  * template : REQUIRED : The character-escaped version of the template based on which you are rendering exported data.
  * profiles : OPTIONAL : list of dictionary returned by the getSampleProfile method

* sendMessageToPartner
  Test the connection to your destination by sending messages to the partner endpoint.
  Optionally, you can send a list of profiles in the request. If you do not send any profiles, Experience Platform generates those internally. 
  In this case, you can view the profiles that were used for validation in the response you receive from your getSampleProfile endpoint.
  Arguments:
  * destinationInstanceId : REQUIRED : Also known as order ID. The ID of the destination instance based on which you are generating sample profiles.
   See documentation for info on how to retrieve it: https://experienceleague.adobe.com/docs/experience-platform/destinations/destination-sdk/api/developer-tools-reference/destination-testing-api.html?lang=en#get-destination-instance-id
  * profiles : OPTIONAL : list of dictionary returned by the getSampleProfile method

* getSubmissions
  List of all destinations submitted for publishing for your IMS Organization

* getSubmission
  Get a specific destination submission status based on the ID passed.
  Argument:
  * destinationConfigId : REQUIRED : The ID of the destination configuration you have submitted for publishing.

* SubmitDestination
  Submit a destination configuration for publishing
  Arguments:
  * destinationObj : REQUIRED : The object defining the destination config. (DestinationId, Access, AllowedOrgs)

* updateSubmissionRequest
  Update the allowed organizations in a destination publish request.
  Arguments:
  * destinationConfigId : REQUIRED : The ID of the destination configuration you have submitted for publishing.
  * destinationObj : REQUIRED : The object defining the destination config. (DestinationId, Access, AllowedOrgs)