# Identity module in aepp

This documentation will provide you some explanation on how to use the identity module and the different methods supported by this module.\
It will include some examples but be aware that not all methods will be documented here.\
To have a full view on the different API endpoints specific to the schema API, please refer to this [API documentation](https://developer.adobe.com/experience-platform-apis/references/identity-service/).\
Alternatively, you can use the docstring in the methods to have more information.

## What is an identity ?

The identity service is a key component of Adobe Experience Platform. The whole system is based on the **users** data that are recognizable by the different identities these users are using during their journey.\
A user coming on the website will probably have a cookie ID that will enable its identification during several sessions, this is an identity (identity A).\
At the same time, if the user is login in to your platform, chances are that (s)he also has a customer ID that can be attached, this would be a second identity (identity B).

Adobe Experience Platform enable the tracking of these identity as their own entity and you can then use them within your schema, independently of their schema field name.\
By defining the identities in an agnostic fashion, you will create an identity graph of the users that will enable AEP to build a 360° view of your users, their different activities (captures in datasets) will be linked together and you will be able to place condition or trigger on the full user profile.

You can see the setup of identities as the Relationship definition of your different user profile in your system.\
You will have, most probably:
* a cookie ID,
* a CRM ID,
* an email address

All of them, when captured 2 by 2,  will build the agnostic profile of the user.

For more information, please refer to the [official documentation on identities](https://experienceleague.adobe.com/docs/experience-platform/identity/home.html?lang=en)

### Default Identities

Adobe Experience Platform provides default identities:

* Cookie ID: Cookie IDs identify web browsers. These identities are critical for expansion and constitute the majority of the identity graph. However, by nature they decay fast and lose their value over time.
* Cross-Device ID: Cross-device IDs identify an individual and usually tie other IDs together. Examples include a login ID, CRM ID, and loyalty ID. This is an indication to Identity Service to handle the value sensitively.
* Device ID: Device IDs identify hardware devices, such as IDFA (iPhone and iPad), GAID (Android), and RIDA (Roku), and can be shared by multiple people in households.
* Email address:Email addresses are often associated with a single person and therefore can be used to identify that person across different channels. Identities of this type include personally identifiable information (PII). This is an indication to Identity Service to handle the value sensitively.
* Phone number: Phone numbers are often associated with a single person and therefore can be used to identify that person across different channels. Identities of this type include PII. This is indication to Identity Service to handle the value sensitively.
* Non-people identifier: Non-people IDs are used for storing identifiers that require namespaces but are not connected to a person cluster. For example, a product SKU, data related to products, organizations, or stores.

The Non-people identifier is helpful for usage of link relationship that are not refering a user. You can see them as lookup tables **compatible for real time decisioning**. The setup of these Non people identifier is mandatory if you want to use real-time decisioning on data that have a relationship (segment or condition). You can always linked the data via Query Service if this is not required to have it connected in real time or within a segment.\ 
Customer Journey Analytics doesn't require you to create these relationship for building lookup table.

Adobe Experience Platform provides default 3rd party identities. These identities could be created as custom ones, but using the default namespace provided by AEP would bring additional native features from AEP available.\
You can find the list of the namespace provided [here](https://experienceleague.adobe.com/docs/experience-platform/identity/namespaces.html?lang=en#managing-custom-namespaces).

## Importing the module

Before importing the module, you would need to import the configuration file, or alternatively provide the information required for the API connection through the configure method. [see getting starting](./getting-started.md)

To import the module you can use the import statement with the `identity` keyword.

```python
import aepp
aepp.importConfigFile('myConfig_file.json')

from aepp import identity
```

The identity module provides a class that you can use for generating and retrieving identities.\
The following documentation will provide you with more information on its usage.

## The Identity class

The Identity class is the default API connector that you would encounter for any other submodules on this python module.\
This class can be instantiated by calling the `Identity()` from the `identity` module.

Following the previous method described above, you can realize this:

```python
myIds = identity.Identity(region='va7')
```

3 parameters are possible for the instantiation of the class:

* region : **REQUIRED** : The region to be used for identity database. By default, the NLD2 will be selected. (other choice : va7)
* config : OPTIONAL : config object in the config module. (example : aepp.config.config_object)
* header : OPTIONAL : header object  in the config module. (example: aepp.config.header)

### Region parameter

When instanciating the Identity class, you need to provide a region (if not the NLD2 region will be selected by default).\
Due to GDPR and different legal regulation, Adobe has different datacenters where they store their identity graph relationships.
Therefore, you will need to inform the connector which region you want to connect to.
The different regions available are:

* NLD2 : Europe (Amsterdam data center)
* VA7 : US / World (Virginia data center)

### Using kwargs

Any additional keywords parameters used will update the header used within the requests with new parameter.
It can be useful when you want to connect to multiple sandboxes with the same JWT authentication.\
In that case, the 2 instances will be created as such:

```python
myIds1 = queryservice.Identity({"region":"va7","x-sandbox-name":"mySandbox1"})
```

```python
myIds2 = queryservice.Identity({"region":"va7","x-sandbox-name":"mySandbox2"})
```

**Note**: Sandbox can be setup in the configuration file and when calling the `configure` method.

## Identity use-cases

You can use the identity module for the following use-cases:

### Get your Identity

It may be useful for you to identify what identity has been setup on your AEP instance.\
In order to do that, you can simply run the `getIdentites` method.\
Because you may be interested only on the identity that **YOU** have setup, you can pass the parameter `only_custom` to achieve this.

```python
import aepp

aepp.importConfigFile('myConfigFile.json')

from aepp import identity

myIds = identity.Identity() ## by default the nld2 region
resultIds = myIds.getIdentites(only_custom=True)
## this will result in a list.
```

### Create new identities

You can create new identity by using the method `createIdentity`.\
You will need to provide at least:

* a name
* a code
* a type; the type can only be one of those: COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE or PHONE.

Please refer to the docstring for more information.

**Important**: You cannot delete an identity once it has been created!

### Get cluster of IDs for a specific ID

The identity endpoint can give you the ID graph attached to an ID.\
You can access this information by using the `getClustersMembers` or `getIdentityMapping`.

Docstring of these methods:

**getClusterHistory**
Given an XID, return all cluster associations with that XID.\
It is required to pass either xid or (namespace/nsid & id) pair to get cluster history.\
Arguments:\
* xid : REQUIRED : Identity string returns by the getIdentity method.
* nsid : OPTIONAL : namespace id (default : 411)
* namespace : OPTIONAL : namespace code. (default : adcloud)
* id_value : OPTIONAL : ID of the customer in given namespace.
* graphType : OPTIONAL : Graph type (output type) you want to get the cluster from. (default private)


**getIdentityMapping**
Given an XID, returns all XID mappings in the requested namespace (targetNs).\
It is required to pass either xid or (namespace/nsid & id) pair to get mappings in required namespace.\
Arguments:\
* xid : REQUIRED : Identity string returns by the getIdentity method.
* nsid : OPTIONAL : namespace id (default : 411)
* namespace : OPTIONAL : namespace code. (default : adcloud)
* id_value : OPTIONAL : ID of the customer in given namespace.
* graphType : OPTIONAL : Graph type (output type) you want to get the cluster from. (default private)
* targetNs : OPTIONAL : The namespace you want to get the mappings from.
