#!/usr/bin/env python

"""Test suite for the device class."""

import unittest
from graphene.test import Client
from tangogql.schema import tangoschema
import queries


class TestDeviceClass(unittest.TestCase):
    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self, query):
        return (self.client.execute(query))['data']

    def test_device_resolve_name(self):
        result = self.execute(queries.device_name)
        assert 'devices' in result
        assert "name" in result['devices'][0]
        assert "sys/tg_test/1" == result['devices'][0]['name']

    def test_device_resolve_state(self):
        result = self.execute(queries.device_state)
        assert 'devices' in result
        result = result['devices'][0]
        assert isinstance(result['state'], str)
        assert len(result['state']) > 0

    def test_device_resolve_properties(self):
        result = self.execute(queries.device_properties)
        assert 'devices' in result
        result = result['devices'][0]
        assert isinstance(result['properties'], list)
        result = result['properties'][0]
        assert isinstance(result, dict)
        assert "name" in result
        assert "device" in result
        assert "value" in result

    def test_device_resolve_attributes(self):
        result = self.execute(queries.device_attributes)
        assert 'devices' in result
        result = result['devices'][0]
        assert isinstance(result['attributes'], list)
        result = result['attributes'][0]
        assert isinstance(result, dict)
        assert "name" in result
        assert "device" in result
        assert "datatype" in result
        assert "dataformat" in result
        assert "writable" in result
        assert "label" in result
        assert "unit" in result
        assert "description" in result
        assert "value" in result
        assert "quality" in result
        for key, value in result.items():
            if key != 'value':
                assert isinstance(value, str)
            else:
                assert isinstance(value, (int, float))

    def test_device_resolve_commands(self):
        result = self.execute(queries.device_commands)
        assert 'devices' in result
        result = result['devices'][0]
        assert isinstance(result['commands'], list)
        result = result['commands'][0]
        assert isinstance(result, dict)
        assert "name" in result
        assert "tag" in result
        assert "displevel" in result
        assert "intype" in result
        assert "intypedesc" in result
        assert "outtype" in result
        assert "outtypedesc" in result
        for key, value in result.items():
            if key != 'tag':
                assert isinstance(value, str)
            else:
                assert isinstance(value, (int, float))

    def test_device_resolve_server(self):
        result = self.execute(queries.device_server)
        assert 'devices' in result
        result = result['devices'][0]
        assert isinstance(result['server'], list)
        result = result['server'][0]
        assert isinstance(result, dict)
        assert "id" in result
        assert "host" in result
        for key, value in result.items():
            assert isinstance(value, str)

    def test_device_resolve_pid(self):
        result = self.execute(queries.device_pid)
        assert 'devices' in result
        result = result['devices'][0]
        assert isinstance(result['pid'], int)

    def test_device_resolve_startedDate(self):
        result = self.execute(queries.device_startedDate)
        assert 'devices' in result
        result = result['devices'][0]
        assert isinstance(result['startedDate'], str)

    def test_device_resolve_stoppedDate(self):
        result = self.execute(queries.device_stoppedDate)
        assert 'devices' in result
        result = result['devices'][0]
        assert isinstance(result['stoppedDate'], str)


class TestDomainClass(unittest.TestCase):
    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self, query):
        return (self.client.execute(query))['data']

    def test_domain_resolve_name(self):
        result = self.execute(queries.domain_name)
        assert 'domains' in result
        assert "name" in result['domains'][0]
        result = result['domains'][0]
        for key, value in result.items():
            assert isinstance(value, str)

    def test_domain_resolve_families(self):
        result = self.execute(queries.domain_families)
        assert 'domains' in result
        result = result['domains'][0]
        assert "families" in result
        result = result['families'][0]
        assert "name"in result
        assert "domain" in result
        assert "members" in result

        assert isinstance(result['name'], str)
        assert isinstance(result['domain'], str)

        result = result['members'][0]
        assert "name" in result and isinstance(result['name'], str)
        assert "state" in result and isinstance(result['state'], str)
        assert "pid" in result and isinstance(result['pid'], int)
        assert "startedDate" in result and isinstance(result['startedDate'], str)
        assert "stoppedDate" in result and isinstance(result['stoppedDate'], str)
        assert "exported" in result and isinstance(result['exported'], bool)
        assert "domain" in result and isinstance(result['domain'], str)
        assert "family" in result and isinstance(result['family'], str)


class TestMemberClass(unittest.TestCase):
    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self, query):
        return (self.client.execute(query))['data']

    def test_member_resolve_name(self):
        result = self.execute(queries.member_name)
        assert 'members' in result
        result = result['members'][0]
        assert 'name' in result
        assert isinstance(result['name'], str)

    def test_member_resolve_state(self):
        result = self.execute(queries.member_state)
        assert 'members' in result
        result = result['members'][0]
        assert 'state' in result
        assert isinstance(result['state'], str)

    # """ def test_member_resolve_deviceClass(self):
    #     result = self.execute(queries.member_deviceClass)
    #     assert ('members' in result)
    #     result = result['members'][0]
    #     assert ('deviceClass' in result)
    #     assert (isinstance(result['deviceClass'],str)) """

    def test_member_resolve_pid(self):
        result = self.execute(queries.member_pid)
        assert 'members' in result
        result = result['members'][0]
        assert 'pid' in result
        assert isinstance(result['pid'], int)

    def test_member_resolve_startedDate(self):
        result = self.execute(queries.member_startedDate)
        assert 'members' in result
        result = result['members'][0]
        assert 'startedDate' in result
        assert isinstance(result['startedDate'], str)

    def test_member_resolve_stoppedDate(self):
            result = self.execute(queries.member_stoppedDate)
            assert 'members' in result
            result = result['members'][0]
            assert 'stoppedDate' in result
            assert isinstance(result['stoppedDate'], str)

    def test_member_resolve_exported(self):
            result = self.execute(queries.member_exported)
            assert 'members' in result
            result = result['members'][0]
            assert 'exported' in result
            assert isinstance(result['exported'], bool)

    def test_member_resolve_domain(self):
        result = self.execute(queries.member_domain)
        assert 'members' in result
        result = result['members'][0]
        assert 'domain' in result
        assert isinstance(result['domain'], str)

    def test_member_resolve_family(self):
        result = self.execute(queries.member_family)
        assert 'members' in result
        result = result['members'][0]
        assert 'family' in result
        assert isinstance(result['family'], str)


# Test of mutation classes
class TestPutDevicePropertyClass(unittest.TestCase):

    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self, query):
        return (self.client.execute(query))['data']

    def test_putDeviceProperty_mutate(self):
        result = self.execute(queries.putDeviceProperty)
        assert "putDeviceProperty" in result
        result = result['putDeviceProperty']
        assert "ok" in result and isinstance(result['ok'], bool)
        assert "message"in result and isinstance(result['message'], list)
        for m in result['message']:
            assert (isinstance(m, str))


class TestDeleteDevicePropertyClass(unittest.TestCase):

    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return (self.client.execute(query))['data']

    def test_DeleteDeviceProperty_mutate(self):
        result = self.execute(queries.deleteDeviceProperty)
        assert "deleteDeviceProperty" in result
        result = result['deleteDeviceProperty']
        assert "ok" in result and isinstance(result['ok'], bool)
        assert "message"in result and isinstance(result['message'], list)
        for m in result['message']:
            assert (isinstance(m, str))


class TestExecuteDeviceCommandClass(unittest.TestCase):

    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return (self.client.execute(query))['data']

    def test_ExecuteDeviceCommand_mutate(self):
        result = self.execute(queries.executeDeviceCommand)
        assert "executeCommand" in result
        result = result['executeCommand']
        assert "ok" in result and isinstance(result['ok'], bool)
        assert result['ok']
        assert "output" in result and isinstance(result['output'],
                                                 (str, bool, int, float))
        assert "message"in result and isinstance(result['message'], list)
        assert result["message"][0] == "Success"
    
    def test_ExecuteDeviceCommand_mutate_wrong_input_type(self):
        result = self.execute(queries.executeDeviceCommand_wrong_input_type)
        assert "executeCommand" in result
        result = result['executeCommand']
        assert "ok" in result and isinstance(result['ok'], bool)
        assert result['ok'] is False
        assert "message"in result and isinstance(result['message'], list)
        for m in result['message']:
            assert isinstance(m, str)
        assert result["message"][0] == "The input value is not of acceptable types"
        assert result["output"] is None
    
    def test_ExecuteDeviceCommand_mutate_none_exist_command(self):
        result = self.execute(queries.executeDeviceCommand_none_exist_command)
        assert "executeCommand" in result
        result = result['executeCommand']
        assert "ok" in result and isinstance(result['ok'], bool)
        assert result['ok'] is False
        assert result["output"] is None
        assert "message"in result and isinstance(result['message'], list)
        for m in result['message']:
            assert isinstance(m, str)
        result = result["message"]
        assert result[0] == "Command dfg not found" 
        assert result[1] == "API_CommandNotFound"


class TestSetAttributeValueClass(unittest.TestCase):

    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return (self.client.execute(query))['data']

    def test_setAttributeValue_mutate_none_exist_attr(self):
        result = self.execute(queries.setAttributeValue_none_exist_attr)
        assert "setAttributeValue" in result
        result = result['setAttributeValue']
        assert "ok" in result and isinstance(result['ok'], bool)
        assert result['ok'] is False
        assert "message"in result and isinstance(result['message'], list)
        for m in result['message']:
            assert isinstance(m, str)

    def test_setAttributeValue_mutate(self):
        result = self.execute(queries.setAttributeValue)
        assert "setAttributeValue" in result
        result = result['setAttributeValue']
        assert "ok" in result and isinstance(result['ok'], bool)
        assert result['ok']
        assert "message"in result and isinstance(result['message'],list)
        for m in result['message']:
            assert isinstance(m, str)
        assert result["message"][0] == "Success"

    def test_setAttributeValue_mutate_wrong_input_type(self):
            result = self.execute(queries.setAttributeValue_wrong_input_type)
            assert "setAttributeValue" in result
            result = result['setAttributeValue']
            assert "ok" in result and isinstance(result['ok'], bool)
            assert result['ok'] is False
            assert "message"in result and isinstance(result['message'], list)
            for m in result['message']:
                assert (isinstance(m, str))


if __name__=='__main__':
    unittest.main()
