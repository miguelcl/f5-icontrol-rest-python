# Copyright 2015-2016 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

'''This test suite attempts to test the things that a real BIGIP device is
required for that unit testing cannot test.  For example the unit tests can
cover the case in which the beginning of the URL is correct up to the
collection object i.e. https://192.168.1.1/mgmt/tm/  It cannot test that
the collection objects that are after that are correct
i.e https://192.168.1.1/mgmt/tm/boguscollection
'''

from icontrol.session import iControlRESTSession
from requests.exceptions import HTTPError

from pprint import pprint as pp
import pytest
import time

nat_data = {
    'name': 'foo',
    'partition': 'Common',
    'originatingAddress': '192.168.1.1',
    'translationAddress': '192.168.2.1',
}


def teardown_nat(request, icr, url, name, partition):
    '''Remove the nat object that we create during a test '''
    def teardown():
        icr.delete(url, uri_as_parts=True, name=name, partition=partition)
    request.addfinalizer(teardown)


def invalid_url(func, url):
    '''Reusable test to make sure that we get 404 for invalid URL '''
    with pytest.raises(HTTPError) as err:
        func(url)
    return (err.value.response.status_code == 404 and
            'Unexpected Error: Not Found for uri: ' + url
            in str(err.value))


def invalid_credentials(user, password, url):
    '''Reusable test to make sure that we get 401 for invalid creds '''
    icr = iControlRESTSession(user, password)
    with pytest.raises(HTTPError) as err:
        icr.get(url)
    return (err.value.response.status_code == 401 and
            '401 Client Error: F5 Authorization Required' in str(err.value))


def invalid_token_credentials(user, password, url):
    '''Reusable test to make sure that we get 401 for invalid token creds '''
    icr = iControlRESTSession(user, password, token=True)
    with pytest.raises(HTTPError) as err:
        icr.get(url)
    return (err.value.response.status_code == 401 and
            'Authentication required!' in err.value.message)


def test_get(ICR, GET_URL):
    '''Test a GET request to a valid url

    Pass: Returns a 200 with proper json
    '''
    response = ICR.get(GET_URL)
    assert response.status_code == 200
    assert response.json()


def test_get_invalid_url(ICR, FAKE_URL):
    '''Test a GET to an invalid URL.

    Pass: Returns a 404 with a proper message
    '''
    assert invalid_url(ICR.get, FAKE_URL)


def test_post(request, ICR, POST_URL):
    '''Test a POST request to a valid url

    Pass: Returns a 200 and the json object is set correctly
    '''
    teardown_nat(
        request, ICR, POST_URL, nat_data['name'], nat_data['partition'])
    response = ICR.post(POST_URL, json=nat_data)
    response_data = response.json()
    assert response.status_code == 200
    assert(response_data['name'] == nat_data['name'])
    assert(response_data['partition'] == nat_data['partition'])
    assert(response_data['originatingAddress'] ==
           nat_data['originatingAddress'])
    assert(response_data['translationAddress'] ==
           nat_data['translationAddress'])


def test_post_invalid_url(ICR, FAKE_URL):
    '''Test a POST request to an invalid url.

    Pass: Returns a 404 with a proper message
    '''
    assert invalid_url(ICR.post, FAKE_URL)


def test_put(request, ICR, POST_URL):
    '''Test a PUT request to a valid url.

    Pass: Returns a 200 and the json object is set correctly
    '''
    data = {'originatingAddress': '192.168.1.50'}
    teardown_nat(
        request, ICR, POST_URL, nat_data['name'], nat_data['partition'])
    ICR.post(POST_URL, json=nat_data)
    response = ICR.put(
        POST_URL,
        name=nat_data['name'],
        partition=nat_data['partition'],
        uri_as_parts=True,
        json=data)
    response_data = response.json()
    assert response.status_code == 200
    assert response_data['originatingAddress'] == data['originatingAddress']
    assert response_data['name'] == nat_data['name']
    assert response_data['partition'] == nat_data['partition']
    assert response_data['translationAddress'] == \
        nat_data['translationAddress']


def test_put_invalid_url(ICR, FAKE_URL):
    '''Test a PUT request to an invalid url.

    Pass: Return a 404 with a proper error message
    '''
    assert invalid_url(ICR.put, FAKE_URL)


def test_patch(request, ICR, POST_URL):
    '''Test a PATCH request to a valid url.

    Pass: Returns a 200 and the json object is set correctly
    '''
    data = {'originatingAddress': '192.168.1.50'}
    teardown_nat(
        request, ICR, POST_URL, nat_data['name'], nat_data['partition'])
    ICR.post(POST_URL, json=nat_data)
    response = ICR.patch(
        POST_URL,
        name=nat_data['name'],
        partition=nat_data['partition'],
        uri_as_parts=True,
        json=data)
    response_data = response.json()
    assert response.status_code == 200
    assert response_data['originatingAddress'] == data['originatingAddress']
    assert response_data['name'] == nat_data['name']
    assert response_data['partition'] == nat_data['partition']
    assert response_data['translationAddress'] == \
        nat_data['translationAddress']


def test_patch_invalid_url(ICR, FAKE_URL):
    '''Test a PATCH request to an invalid url.

    Pass: Return a 404 with a proper error message
    '''
    assert invalid_url(ICR.patch, FAKE_URL)


def test_delete(request, ICR, POST_URL):
    '''Test a DELETE request to a valid url.

    Pass: Return a 200 and the json is empty.  Subsequent GET returns a 404
    error because the object is no longer found.
    '''
    ICR.post(POST_URL, json=nat_data)
    response = ICR.delete(
        POST_URL,
        name=nat_data['name'],
        partition=nat_data['partition'],
        uri_as_parts=True)
    assert response.status_code == 200
    with pytest.raises(ValueError):
        response.json()

    with pytest.raises(HTTPError) as err:
        ICR.get(
            POST_URL,
            name=nat_data['name'],
            partition=nat_data['partition'],
            uri_as_parts=True)
    pp(err.value.response.status_code)
    assert err.value.response.status_code == 404


def test_delete_invalid_url(ICR, FAKE_URL):
    '''Test a DELETE request to an invalid url.

    Pass: Return a 404 with a proper error message
    '''
    assert invalid_url(ICR.delete, FAKE_URL)


def test_invalid_user(opt_password, GET_URL):
    '''Test login with an invalid username and valid password

    Pass: Returns 401 with authorization required message
    '''
    invalid_credentials('fakeuser', opt_password, GET_URL)


def test_invalid_password(opt_username, GET_URL):
    '''Test login with a valid username and invalid password

    Pass: Returns 401 with authorization required message
    '''
    invalid_credentials(opt_username, 'fakepassword', GET_URL)


def test_token_auth(opt_username, opt_password, GET_URL):
    icr = iControlRESTSession(opt_username, opt_password, token=True)
    response = icr.get(GET_URL)
    assert response.status_code == 200


def test_token_auth_twice(opt_username, opt_password, GET_URL):
    icr = iControlRESTSession(opt_username, opt_password, token=True)
    assert icr.session.auth.attempts == 0
    response = icr.get(GET_URL)
    assert response.status_code == 200
    assert icr.session.auth.attempts == 1
    response = icr.get(GET_URL)
    assert response.status_code == 200
    # This token should still be valid, so we should reuse it.
    assert icr.session.auth.attempts == 1


def test_token_auth_expired(opt_username, opt_password, GET_URL):
    icr = iControlRESTSession(opt_username, opt_password, token=True)
    assert icr.session.auth.attempts == 0
    response = icr.get(GET_URL)
    assert response.status_code == 200
    assert icr.session.auth.attempts == 1
    assert icr.session.auth.expiration >= time.time()

    # Artificially expire the token
    icr.session.auth.expiration = time.time() - 1.0

    # Since token is expired, we should get a new one.
    response = icr.get(GET_URL)
    assert response.status_code == 200
    assert icr.session.auth.attempts == 2


def test_token_invalid_user(opt_password, GET_URL):
    invalid_token_credentials('fakeuser', opt_password, GET_URL)


def test_token_invalid_password(opt_username, GET_URL):
    invalid_token_credentials(opt_username, 'fakepassword', GET_URL)


# You must configure a user that has a non-admin role in a partition for
# test_nonadmin tests to be effective.  For instance:
#
# auth user bob {
#    description bob
#    encrypted-password $6$LsSnHp7J$AIJ2IC8kS.YDrrn/sH6BsxQ...
#    partition Common
#    partition-access {
#        bobspartition {
#            role operator
#        }
#    }
#    shell tmsh
# }
#
# Then instantiate with --nonadmin-username=bob --nonadmin-password=changeme
def test_nonadmin_token_auth(opt_nonadmin_username, opt_nonadmin_password,
                             GET_URL):
    if not opt_nonadmin_username or not opt_nonadmin_password:
        pytest.skip("No non-admin username/password configured")
    icr = iControlRESTSession(opt_nonadmin_username,
                              opt_nonadmin_password,
                              token=True)
    response = icr.get(GET_URL)
    assert response.status_code == 200


def test_nonadmin_token_auth_invalid_password(opt_nonadmin_username,
                                              GET_URL):
    if not opt_nonadmin_username:
        pytest.skip("No non-admin username/password configured")
    invalid_token_credentials(opt_nonadmin_username,
                              'fakepassword',
                              GET_URL)


def test_nonadmin_token_auth_invalid_username(opt_nonadmin_password,
                                              GET_URL):
    if not opt_nonadmin_password:
        pytest.skip("No non-admin username/password configured")
    invalid_token_credentials('fakeuser',
                              opt_nonadmin_password,
                              GET_URL)
