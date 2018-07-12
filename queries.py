device_name = '''query{devices(pattern: "sys/tg_test/1"){name}}'''

device_state = """query{devices(pattern: "sys/tg_test/1"){state}}"""

device_properties = """query{devices(pattern: "sys/tg_test/1"){properties(pattern:"Do_not_remove_this"){name,device,value}}}"""


device_attributes = """ query{devices(pattern: "sys/tg_test/1"){attributes(pattern:"ampli"){
                                    name,
                                    device,
                                    datatype,
                                    dataformat,
                                    writable,
                                    label,
                                    unit,
                                    description,
                                    value,
                                    quality,
                                    }}}"""
                                    
device_commands = """ query{devices(pattern: "sys/tg_test/1"){commands(pattern:"DevBoolean"){
                                name,
                                tag
                                displevel,
                                intype,
                                intypedesc,
                                outtype,
                                outtypedesc}}} """

device_server = """query{devices(pattern: "sys/tg_test/1"){server{id,host}}}  """

device_pid = """query{devices(pattern: "sys/tg_test/1"){pid}}"""

device_startedDate = """ query{devices(pattern: "sys/tg_test/1"){startedDate}} """

device_stoppedDate= """ query{devices(pattern: "sys/tg_test/1"){stoppedDate}} """

domain_name = """ query{domains(pattern: "*"){name}} """

domain_families = """query{domains(pattern: "sys"){
    families(pattern: "*"){
            name,
            domain,
            members(pattern:"*"){
                name,
            state,
            deviceClass,
            pid,
            startedDate,
            stoppedDate,
            exported,
            domain,
            family
            } 
        }
    }}"""

member_name = """ query{members(pattern:"0"){name}}"""

member_state = """ query{members(pattern:"0"){state}}"""
member_deviceClass = """ query{members(pattern:"0"){deviceClass}}"""
member_pid = """ query{members(pattern:"0"){pid}}"""
member_startedDate = """ query{members(pattern:"0"){startedDate}}"""
member_stoppedDate = """ query{members(pattern:"0"){stoppedDate} }"""
member_exported = """ query{members(pattern:"0"){stoppedDate} }"""
member_domain = """ query{members(pattern:"0"){domain}}"""
member_family = """ query{members(pattern:"0"){family}}"""
# mutations
putDeviceProperty = """mutation{putDeviceProperty(device : "sys/tg_test/1" name: "sommar" value: "solig"){ok,message}}"""
deleteDeviceProperty = """mutation{deleteDeviceProperty(device : "Hej" name: "sommar"){ok,message}}"""
executeDeviceCommand = """mutation{executeCommand(device : "sys/tg_test/1" command: "DevBoolean" argin: 1){ok,message,output}}"""

executeDeviceCommand_wrong_input_type = """ mutation{executeCommand(device : "sys/tg_test/1" command: "DevBoolean" argin: sdfsdf){
  ok,
  message,
output
}} """
executeDeviceCommand_none_exist_command = """ mutation{executeCommand(device : "sys/tg_test/1" command: "dfg" argin: 1){
  ok,
  message,
output
}} """

setAttributeValue = """mutation{setAttributeValue(device : "sys/tg_test/1" name: "ampli" value: 1){
  ok,
  message,

}}"""

setAttributeValue_wrong_input_type = """ mutation{setAttributeValue(device : "sys/tg_test/1" name: "ampli" value: dsf){
  ok,
  message,

}} """

setAttributeValue_none_exist_attr = """mutation{setAttributeValue(device : "sys/tg_test/1" name: "sdfa" value: 1){
  ok,
  message,

}} """

setAttributeValue_none_exist_device = """mutation{setAttributeValue(device : "sys/xfs/1" name: "ampli" value: 1){
  ok,
  message,

}} """