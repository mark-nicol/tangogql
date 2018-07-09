import unittest
from graphene.test import Client
from schema import tangoschema
import queries
class TestDeviceClass(unittest.TestCase):
    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return  (self.client.execute(query))['data']

    def test_device_resolve_name(self):
        result = self.execute(queries.device_name)
        assert ('devices' in result) == True
        assert ("name"  in result['devices'][0]) == True
        assert "sys/tg_test/1" == result['devices'][0]['name']

    def test_device_resolve_state(self):
        result = self.execute(queries.device_state)
        assert ('devices' in result) == True 
        result = result['devices'][0]
        assert isinstance(result['state'],str) == True
        assert len(result['state']) > 0 

    def test_device_resolve_properties(self):
        result = self.execute(queries.device_properties)
        assert ('devices' in result) == True 
        result = result['devices'][0]
        assert isinstance(result['properties'],list) == True
        result = result ['properties'][0]
        assert isinstance(result,dict) == True
        assert ("name" in result) == True
        assert ("device" in result) == True
        assert ("value" in result) == True 

    def test_device_resolve_attributes(self):
        result = self.execute(queries.device_attributes)
        assert ('devices' in result) == True 
        result = result['devices'][0]
        assert isinstance(result['attributes'],list) == True
        result = result ['attributes'][0]
        assert isinstance(result,dict) == True
        assert ("name" in result) == True
        assert ("device" in result) == True
        assert ("datatype" in result) == True
        assert ("dataformat" in result) == True
        assert ("writable" in result) == True
        assert ("label" in result) == True
        assert ("unit" in result) == True
        assert ("description" in result) == True
        assert ("value" in result) == True
        assert ("quality" in result) == True
        for key, value in result.items():
            if key != 'value':
                assert isinstance (value, str)
            else:
                assert isinstance (value, (int,float))    
    
    def test_device_resolve_commands(self):
        result = self.execute(queries.device_commands)
        assert ('devices' in result) == True 
        result = result['devices'][0]
        assert isinstance(result['commands'],list) == True
        result = result ['commands'][0]
        assert isinstance(result,dict) == True
        assert ("name" in result) == True
        assert ("tag" in result) == True
        assert ("displevel" in result) == True
        assert ("intype" in result) == True
        assert ("intypedesc" in result) == True
        assert ("outtype" in result) == True
        assert ("outtypedesc" in result) == True
        for key, value in result.items():
            if key != 'tag':
                assert isinstance (value, str)
            else:
                assert isinstance (value, (int,float))    

    def test_device_resolve_server(self):
        result = self.execute(queries.device_server)
        assert ('devices' in result) == True 
        result = result['devices'][0]
        assert isinstance(result['server'],list) == True
        result = result ['server'][0]
        assert isinstance(result,dict) == True
        assert ("id" in result) == True
        assert ("host" in result) == True
        for key, value in result.items():
            assert isinstance (value, str)

    def test_device_resolve_pid(self):
        result = self.execute(queries.device_pid)
        assert ('devices' in result) == True 
        result = result['devices'][0]
        assert isinstance(result['pid'],int) == True

    def test_device_resolve_startedDate(self):
        result = self.execute(queries.device_startedDate)
        assert ('devices' in result) == True 
        result = result['devices'][0]
        assert isinstance(result['startedDate'],float) == True

    def test_device_resolve_stoppedDate(self):
        result = self.execute(queries.device_stoppedDate)
        assert ('devices' in result) == True 
        result = result['devices'][0]
        assert isinstance(result['stoppedDate'],float) == True
    
class TestDomainClass(unittest.TestCase):
    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return  (self.client.execute(query))['data']

    def test_domain_resolve_name(self):
        result = self.execute(queries.domain_name)
        assert ('domains' in result) == True
        assert ("name"  in result['domains'][0]) == True
        result = result['domains'][0]
        for key,value in result.items():
            assert isinstance(value,str) == True
    
    def test_domain_resolve_families(self):
        result = self.execute(queries.domain_families)
        assert ('domains' in result) == True
        result = result['domains'][0]
        assert ("families"  in result) == True
        result = result['families'][0]
        assert ("name"in result) == True
        assert ("domain" in result) == True
        assert ("members" in result) == True

        assert isinstance(result['name'],str) == True
        assert isinstance(result['domain'],str) == True

        result = result['members'][0]
        assert (("name" in result) == True and isinstance(result['name'], str) == True)
        assert (("state" in result) == True and isinstance(result['state'], str) == True)
        assert (("devicesClass" in result) == True and isinstance(result['deviceClass'], str) == True)
        assert (("pid" in result) == True and isinstance(result['pid'], int) == True)
        assert (("startedDate" in result) == True and isinstance(result['startedDate'], float)== True)
        assert (("startedDate" in result) == True and isinstance(result['startedDate'], float)== True)
        assert (("stoppedDate" in result) == True and isinstance(result['stoppedDate'], float)== True)
        assert (("exported" in result) == True and isinstance(result['exported'], bool)== True)
        assert (("domain" in result) == True and isinstance(result['domain'], str)== True)
        assert (("family" in result) == True and isinstance(result['family'], str)== True)

class TestMemberClass(unittest.TestCase):
    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return  (self.client.execute(query))['data']

    def test_member_resolve_name(self):
        result = self.execute(queries.member_name)
        assert ('members' in result) == True
        result = result['members'][0]
        assert ('name' in result) == True
        assert (isinstance(result['name'],str)) == True
    
    def test_member_resolve_state(self):
        result = self.execute(queries.member_state)
        assert ('members' in result) == True
        result = result['members'][0]
        assert ('state' in result) == True
        assert (isinstance(result['state'],str)) == True
    
    def test_member_resolve_deviceClass(self):
        result = self.execute(queries.member_deviceClass)
        assert ('members' in result) == True
        result = result['members'][0]
        assert ('deviceClass' in result) == True
        assert (isinstance(result['deviceClass'],str)) == True

    def test_member_resolve_pid(self):
        result = self.execute(queries.member_pid)
        assert ('members' in result) == True
        result = result['members'][0]
        assert ('pid' in result) == True
        assert (isinstance(result['pid'],int)) == True

    def test_member_resolve_startedDate(self):
        result = self.execute(queries.member_startedDate)
        assert ('members' in result) == True
        result = result['members'][0]
        assert ('startDate' in result) == True
        assert (isinstance(result['startDate'],float)) == True

    def test_member_resolve_stoppedDate(self):
            result = self.execute(queries.member_stoppedDate)
            assert ('members' in result) == True
            result = result['members'][0]
            assert ('stoppedDate' in result) == True
            assert (isinstance(result['stoppedDate'],float)) == True
    
    def test_member_resolve_exported(self):
            result = self.execute(queries.member_exported)
            assert ('members' in result) == True
            result = result['members'][0]
            assert ('exported' in result) == True
            assert (isinstance(result['exported'],bool)) == True
    
    def test_member_resolve_domain(self):
        result = self.execute(queries.member_domain)
        assert ('members' in result) == True
        result = result['members'][0]
        assert ('domain' in result) == True
        assert (isinstance(result['domain'],str)) == True
    
    def test_member_resolve_family(self):
        result = self.execute(queries.member_family)
        assert ('members' in result) == True
        result = result['members'][0]
        assert ('families' in result) == True
        assert (isinstance(result['families'],str)) == True
    
# Test of mutation classes

class TestPutDevicePropertyClass(unittest.TestCase):

    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return  (self.client.execute(query))['data']

    def test_putDeviceProperty_mutate(self):
        result = self.execute(queries.putDeviceProperty)
        assert ("putDeviceProperty" in result) == True
        result = result['putDeviceProperty']
        assert (("ok" in result) == True and isinstance(result['ok'], bool)) 
        assert (("message"in result) and isinstance(result['message'],list))== True
        for m in result['message']:
            assert (isinstance(m, str)  == True) 

class TestDeleteDevicePropertyClass(unittest.TestCase):

    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return  (self.client.execute(query))['data']

    def test_DeleteDeviceProperty_mutate(self):
        result = self.execute(queries.deleteDeviceProperty)
        assert ("deleteDeviceProperty" in result) == True
        result = result['deleteDeviceProperty']
        assert ("ok" in result) and isinstance(result['ok'], bool) == True 
        assert (("message"in result) and isinstance(result['message'],list))== True
        for m in result['message']:
            assert (isinstance(m, str)  == True) 


class TestExecuteDeviceCommandClass(unittest.TestCase):

    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return  (self.client.execute(query))['data']

    def test_ExecuteDeviceCommand_mutate(self):
        result = self.execute(queries.executeDeviceCommand)
        assert ("executeCommand" in result) == True
        result = result['executeCommand']
        assert ("ok" in result) and isinstance(result['ok'], bool) == True 
        assert result['ok'] == True
        assert (("output" in result) and isinstance(result['output'],(str,bool,int,float))) == True
        assert (("message"in result) and isinstance(result['message'],list))== True
        assert(result["message"][0] == "Success")
    
    def test_ExecuteDeviceCommand_mutate_wrong_input_type(self):
        result = self.execute(queries.executeDeviceCommand_wrong_input_type)
        assert ("executeCommand" in result) == True
        result = result['executeCommand']
        assert ("ok" in result) and isinstance(result['ok'], bool) == True 
        assert result['ok'] == False
        assert (("message"in result) and isinstance(result['message'],list))== True
        for m in result['message']:
            assert (isinstance(m, str)  == True) 
        assert result["message"][0] == "The input value is not of acceptable types"
        assert result["output"] == None
    
    def test_ExecuteDeviceCommand_mutate_none_exist_command(self):
        result = self.execute(queries.executeDeviceCommand_none_exist_command)
        assert ("executeCommand" in result) == True
        result = result['executeCommand']
        assert ("ok" in result) and isinstance(result['ok'], bool) == True 
        assert result['ok'] == False
        assert result["output"] == None
        assert (("message"in result) and isinstance(result['message'],list))== True
        for m in result['message']:
            assert (isinstance(m, str)  == True) 
        result = result["message"]
        assert result[0] == "Command dfg not found" 
        assert result[1] == "API_CommandNotFound"

class TestSetAttributeValueClass(unittest.TestCase):

    def setUp(self):
        self.client = Client(tangoschema)

    def execute(self,query):
        return  (self.client.execute(query))['data']

    def test_setAttributeValue_mutate(self):
        result = self.execute(queries.setAttributeValue)
        assert ("setAttributeValue" in result) == True
        result = result['setAttributeValue']
        assert ("ok" in result) and isinstance(result['ok'], bool) == True 
        assert result['ok'] == True
        assert (("message"in result) and isinstance(result['message'],list))== True
        for m in result['message']:
            assert (isinstance(m, str)  == True) 
        assert result["message"][0] == "Success"

    def test_setAttributeValue_mutate_wrong_input_type(self):
            result = self.execute(queries.setAttributeValue_wrong_input_type)
            assert ("setAttributeValue" in result) == True
            result = result['setAttributeValue']
            assert ("ok" in result) and isinstance(result['ok'], bool) == True 
            assert result['ok'] == False
            assert (("message"in result) and isinstance(result['message'],list))== True
            for m in result['message']:
                assert (isinstance(m, str)  == True) 
    
    def test_setAttributeValue_mutate_none_exist_attr(self):
        result = self.execute(queries.setAttributeValue_none_exist_attr)
        assert ("setAttributeValue" in result) == True
        result = result['setAttributeValue']
        assert ("ok" in result) and isinstance(result['ok'], bool) == True 
        assert result['ok'] == False
        assert (("message"in result) and isinstance(result['message'],list))== True
        for m in result['message']:
            assert (isinstance(m, str)  == True) 

if __name__=='__main__':
    unittest.main()