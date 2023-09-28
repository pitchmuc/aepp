## Publish new version of aepp
 We are currently using PyPI to for storing and distributing aepp packages, you can find the aepp project in https://pypi.org/project/aepp/. In this document, we will go through the steps for publishing new version of aepp. 
 
1. Contact the owner @Julien Piccini to add your PyPI account as the collaborator for the aepp project
2. Set up your api token and save it in your local following the step "To make an API token" in https://pypi.org/help/#apitoken
3. Update the version in aepp/__version__.py and make necessary changes in setup.py under the project root if your changes require dependency update for aepp
4. Add a quick note about what has been changed in the new version you plan to publish in aepp/docs/releases.md
5. Install build and twine in python by running the following command in case you don't have them installed before
```shell
pip install build
pip install twine
```
6. Run the command below to generate two files in a dist folder generated under the project root
```shell
python -m build
```
![release-build.png](docs%2Frelease-build.png)
7. Upload the two files in dist folder by running the command below
```shell
python -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/* 
```
When prompted for username, enter `__token__` as username, and use the api token generated in step 2 as password
![release-upload.png](docs%2Frelease-upload.png)
8. You can find the latest published aepp from https://pypi.org/project/aepp/#history