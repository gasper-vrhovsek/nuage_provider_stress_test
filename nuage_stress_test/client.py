import argparse
import json
import os
import time

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

parser = argparse.ArgumentParser(description='Short sample app')

parser.add_argument('-i', dest="iterations_per_second", default=5, type=int)
parser.add_argument('-t', dest="time", default=10, type=int)


class Rest:
    NUAGE_API_PATH = "/nuage/api/v5_0"

    def __init__(self, url, user, password):
        self.url = url + self.NUAGE_API_PATH
        self.user = user
        self.password = password
        self.headers = {
            'X-Nuage-Organization': 'csp',
            "Content-Type": "application/json; charset=UTF-8"
        }
        self.api_key = ""
        self.enterprise_id = ""

    def login(self):
        login_url = self.url + "/me"
        print "Calling " + login_url
        response = requests.request('get', login_url,
                                    auth=HTTPBasicAuth(self.user, self.password),
                                    headers=self.headers,
                                    verify=False
                                    )

        if response.ok:
            print "Status code = " + str(response.status_code)
            byteifyed_response_json = json_loads_byteified(response.text)
            print byteifyed_response_json

            self.api_key = byteifyed_response_json[0].get('APIKey')
            self.enterprise_id = byteifyed_response_json[0].get('enterpriseID')

            print "APIKey = " + self.api_key
            print "enterpriseID = " + self.enterprise_id
        else:
            print "Blah, you failed!"

    def get_enterprises(self):
        enterprises_url = self.url + "/enterprises"
        return self._request(enterprises_url, 'get')

    def get_subnets(self):
        print "GET subnets"
        subnets_url = self.url + "/subnets"
        return self._request(subnets_url, 'get')

    def get_subnet(self, subnet_id):
        print "GET subnet by id"
        subnets_url = self.url + "/subnets/" + subnet_id
        return self._request(subnets_url, 'get')

    def update_subnet(self, subnet_id, update):
        print "UPDATE subnet"
        subnets_url = self.url + "/subnets/" + subnet_id
        return self._request(subnets_url, 'put', update)

    def delete_subnet(self, subnet_id):
        print "DELETE subnet"
        subnets_url = self.url + "/subnets/" + subnet_id
        return self._request(subnets_url, 'delete')

    def create_subnet(self, zone_id, subnet):
        print "CREATE subnet"
        subnets_url = self.url + "/zones/" + zone_id + "/subnets/"
        return self._request(subnets_url, 'post', subnet)

    def _request(self, url, method, data=None):
        response = requests.request(method, url,
                                    auth=HTTPBasicAuth(self.user, self.api_key),
                                    headers=self.headers,
                                    verify=False,
                                    data=json.dumps(data) if data else None
                                    )
        return response


def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )


def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )


def _byteify(data, ignore_dicts=False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


if __name__ == '__main__':
    # print parser.parse_args()
    parser_results = parser.parse_args()

    freq = parser_results.iterations_per_second
    interval = 1000 / freq
    # print "Interval = " + str(interval)
    duration = parser_results.time

    rest_api = Rest("https://" + os.environ['NUAGE_URL'] + ":8443", os.environ['NUAGE_USERNAME'],
                    os.environ['NUAGE_PASSWORD'])
    rest_api.login()

    start = time.time() * 1000

    count = 0
    while (start + duration * 1000) > (time.time() * 1000):
        it_start = time.time() * 1000
        rest_api.update_subnet("debb9f88-f252-4c30-9a17-d6ae3865e365", {"name": "Subnet test %d" % count})

        count += 1
        it_duration = time.time() * 1000 - it_start
        # print "it_duration = " + str(it_duration)

        if interval > it_duration:
            print "Sleeping for " + str((interval - it_duration) / 1000)
            time.sleep((interval - it_duration) / 1000)

    print "Finished " + str(count) + " requests in " + str(time.time() - start / 1000) + " seconds"
