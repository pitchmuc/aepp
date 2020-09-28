import aepp


def retrieveToken(verbose: bool = False, save: bool = False, **kwargs)->str:
    """ Retrieve the token by using the information provided by the user during the import importConfigFile function. 

    Argument : 
        verbose : OPTIONAL : Default False. If set to True, print information.
    """
    if aepp.config._pathToKey.startswith('/'):
        aepp.config._pathToKey = "."+aepp.config._pathToKey
    with open(aepp.modules.Path(aepp.config._pathToKey), 'r') as f:
        private_key_unencrypted = f.read()
        header_jwt = {'cache-control': 'no-cache',
                      'content-type': 'application/x-www-form-urlencoded'}
    jwtPayload = {
        # Expiration set to 24 hours
        "exp": round(24*60*60 + int(aepp.modules.time.time())),
        "iss": aepp.config.org_id,  # org_id
        "sub": aepp.config.tech_id,  # technical_account_id
        "https://ims-na1.adobelogin.com/s/ent_dataservices_sdk": True,
        "aud": "https://ims-na1.adobelogin.com/c/"+aepp.config.client_id
    }
    encoded_jwt = aepp.modules.jwt.encode(
        jwtPayload, private_key_unencrypted, algorithm='RS256')  # working algorithm
    payload = {
        "client_id": aepp.config.client_id,
        "client_secret": aepp.config._secret,
        "jwt_token": encoded_jwt.decode("utf-8")
    }
    response = aepp.modules.requests.post(aepp.config._TokenEndpoint,
                                          headers=header_jwt, data=payload)
    json_response = response.json()
    token = json_response['access_token']
    aepp.config._token = token
    aepp.config.header.update({"Authorization": "Bearer "+token})
    expire = json_response['expires_in']
    aepp.config.date_limit = aepp.modules.time.time() + expire/1000 - \
        500  # end of time for the token
    if save:
        with open('token.txt', 'w') as f:  # save the token
            f.write(token)
    if verbose == True:
        print('token valid till : ' +
              aepp.modules.time.ctime(aepp.modules.time.time() + expire/1000))
        print('token has been saved here : ' +
              aepp.modules.Path.as_posix(aepp.modules.Path.cwd()))
    return token


def _checkToken(func):
    """    decorator that checks that the token is valid before calling the API    """
    def checking(*args, **kwargs):  # if function is not wrapped, will fire
        now = aepp.modules.time.time()
        if now > aepp.config.date_limit - 1000:
            aepp.config._token = retrieveToken(*args, **kwargs)
            if "headers" in kwargs:
                kwargs['headers']['Authorization'] = "Bearer " + \
                    aepp.config._token
            return func(*args, **kwargs)
        else:  # need to return the function for decorator to return something
            return func(*args, **kwargs)
    return checking  # return the function as object
