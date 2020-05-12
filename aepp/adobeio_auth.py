import aepp
from aepp import config


def retrieveToken(verbose: bool = False, save: bool = False, **kwargs)->str:
    """ Retrieve the token by using the information provided by the user during the import importConfigFile function. 

    Argument : 
        verbose : OPTIONAL : Default False. If set to True, print information.
    """
    if config._pathToKey.startswith('/'):
        config._pathToKey = "."+config._pathToKey
    with open(aepp.Path(config._pathToKey), 'r') as f:
        private_key_unencrypted = f.read()
        header_jwt = {'cache-control': 'no-cache',
                      'content-type': 'application/x-www-form-urlencoded'}
    jwtPayload = {
        # Expiration set to 24 hours
        "exp": round(24*60*60 + int(aepp.time.time())),
        "iss": config._org_id,  # org_id
        "sub": config._tech_id,  # technical_account_id
        "https://ims-na1.adobelogin.com/s/ent_dataservices_sdk": True,
        "aud": "https://ims-na1.adobelogin.com/c/"+config._api_key
    }
    encoded_jwt = aepp.jwt.encode(
        jwtPayload, private_key_unencrypted, algorithm='RS256')  # working algorithm
    payload = {
        "client_id": config._api_key,
        "client_secret": config._secret,
        "jwt_token": encoded_jwt.decode("utf-8")
    }
    response = aepp.requests.post(config._TokenEndpoint,
                                  headers=header_jwt, data=payload)
    json_response = response.json()
    token = json_response['access_token']
    aepp.config._token = token
    aepp.config._header.update({"Authorization": "Bearer "+token})
    expire = json_response['expires_in']
    config._date_limit = aepp.time.time() + expire/1000 - \
        500  # end of time for the token
    if save:
        with open('token.txt', 'w') as f:  # save the token
            f.write(token)
    if verbose == True:
        print('token valid till : ' +
              aepp.time.ctime(aepp.time.time() + expire/1000))
        print('token has been saved here : ' +
              aepp.Path.as_posix(aepp.Path.cwd()))
    return token


def _checkToken(func):
    """    decorator that checks that the token is valid before calling the API    """
    def checking(*args, **kwargs):  # if function is not wrapped, will fire
        config._date_limit
        now = aepp.time.time()
        if now > config._date_limit - 1000:
            config._token = retrieveToken(*args, **kwargs)
            kwargs['headers']['Authorization'] = "Bearer "+config._token
            return func(*args, **kwargs)
        else:  # need to return the function for decorator to return something
            return func(*args, **kwargs)
    return checking  # return the function as object
