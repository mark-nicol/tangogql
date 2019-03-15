"""Module containing the available mutations."""

import PyTango
import logging
import asyncio

from datetime import datetime 
from graphene import ObjectType, Mutation, String, Boolean, List, Field
from tangogql.schema.base import db, proxies
from tangogql.schema.types import ScalarTypes
from tangogql.schema.attribute import DeviceAttribute, collaborative_read_attribute
from tangogql.schema.log import ExcuteCommandUserAction
from tangogql.schema.log import SetAttributeValueUserAction
from tangogql.schema.log import PutDevicePropertyUserAction
from tangogql.schema.log import DeleteDevicePropertyUserAction

logger = logging.getLogger('logger')

from tangogql.schema.log import user_actions

class ExecuteDeviceCommand(Mutation):
    """This class represent a mutation for executing a command."""

    class Arguments:
        device = String(required=True)
        command = String(required=True)
        argin = ScalarTypes()

    ok = Boolean()
    message = List(String)
    output = ScalarTypes()
    
    async def mutate(self, info, device, command, argin=None):
        """ This method executes a command.

        :param device: Name of the device that the command will be executed.
        :type device: str

        :param command: Name of the command
        :type command: str

        :param argin: The input argument for the command
        :type argin: str or int or bool or float

        :return: Return ok = True and message = Success
                 if the command executes successfully, False otherwise.
                 When an input is not one of the scalar types or an exception
                 has been raised while executing the command, it returns
                 message = error_message.
        :rtype: ExecuteDeviceCommand
        """
        
        logger.info("MUTATION - ExecuteDeviceCommand - User: {}, Device: {}, Command: {}, Argin: {}".format(info.context["client"].user, device, command, argin))
        log = ExcuteCommandUserAction(
                                        timestamp = datetime.now(), 
                                        user = info.context["client"].user,
                                        device = device,
                                        name = command,
                                        argin = argin
                                    )
        user_actions.put(log)
        if type(argin) is ValueError:
            return ExecuteDeviceCommand(ok=False, message=[str(argin)])
        try:
            proxy = proxies.get(device)
            result = await proxy.command_inout(command, argin)
            return ExecuteDeviceCommand(ok=True,
                                        message=["Success"],
                                        output=result)
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return ExecuteDeviceCommand(ok=False, message=[e.desc, e.reason])
        except Exception as e:
            return ExecuteDeviceCommand(ok=False, message=[str(e)])


class SetAttributeValue(Mutation):
    """This class represents the mutation for setting value to an attribute."""

    class Arguments:
        device = String(required=True)
        name = String(required=True)
        value = ScalarTypes(required=True)

    ok = Boolean()
    message = List(String)
    attribute = Field(DeviceAttribute)

    async def mutate(self, info, device, name, value):
        """ This method sets value to an attribute.

        :param device: Name of the device
        :type device: str

        :param name: Name of the attribute
        :type name: str
        :param value: The value to be set
        :type value: int, str, bool or float

        :return: Return ok = True and message = Success if successful,
                 False otherwise.
                 When an input is not one the scalar types or an exception has
                 been raised while setting the value returns
                 message = error_message.
        :rtype: SetAttributeValue
        """
      
        logger.info("MUTATION - SetAttributeValue - User: {}, Device: {}, Attribute: {}, Value: {}".format(info.context["client"].user, device, name, value))
        
        if type(value) is ValueError:
            return SetAttributeValue(ok=False, message=[str(value)], attribute=None)
        try:
            proxy = proxies.get(device)
            before = await collaborative_read_attribute(proxy,name)
            read_coro = proxy.write_read_attribute(name, value)
            read_fut = asyncio.ensure_future(read_coro)
            result = await read_fut

            log = SetAttributeValueUserAction(
                                            timestamp = datetime.now(), 
                                            user = info.context["client"].user,
                                            device = device,
                                            name = name,
                                            value = value,
                                            value_before = before.value,
                                            value_after = result.value
                                        )
            user_actions.put(log)

            return SetAttributeValue(ok=True, message=["Success"], attribute=DeviceAttribute(
                name=name,
                device=device,
                _attr_read=read_fut
            ))

        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return SetAttributeValue(ok=False, message=[e.desc, e.reason], attribute=None)
        except Exception as e:
            return SetAttributeValue(ok=False, message=[str(e)], attribute=None)


class PutDeviceProperty(Mutation):
    """This class represents mutation for putting a device property."""

    class Arguments:
        device = String(required=True)
        name = String(required=True)
        value = List(String)
        # async = Boolean()

    ok = Boolean()
    message = List(String)

    def mutate(self, info, device, name, value=""):
        """ This method adds property to a device.

        :param device: Name of a device
        :type device: str
        :param name: Name of the property
        :type name: str
        :param value: Value of the property
        :type value: str

        :return: Returns ok = True and message = Success if successful,
                 False otherwise.
                 If an exception has been raised returns
                 message = error_message.
        :rtype: PutDeviceProperty
        """
        
        logger.info("MUTATION - PutDeviceProperty - User: {}, Device: {}, Name: {}, Value: {}".format(info.context["client"].user, device, name, value))
        # wait = not args.get("async")
        try:
            
            db.put_device_property(device, {name: value})
            log = PutDevicePropertyUserAction(
                                            timestamp = datetime.now(), 
                                            user = info.context["client"].user,
                                            device = device,
                                            name = name,
                                            value = value
                                        )
            user_actions.put(log)
            return PutDeviceProperty(ok=True, message=["Success"])
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return PutDeviceProperty(ok=False, message=[e.desc, e.reason])
        except Exception as e:
            return PutDeviceProperty(ok=False, message=[str(e)])
        

class DeleteDeviceProperty(Mutation):
    """This class represents mutation for deleting property of a device."""

    class Arguments:
        device = String(required=True)
        name = String(required=True)

    ok = Boolean()
    message = List(String)

    def mutate(self, info, device, name):
        """This method delete a property of a device.

        :param device: Name of the device
        :type device: str
        :param name: Name of the property
        :type name: str

        :return: Returns ok = True and message = Success if successful,
                 ok = False otherwise.
                 If exception has been raised returns message = error_message.
        :rtype: DeleteDeviceProperty
        """
        logger.info("MUTATION - DeleteDeviceProperty - User: {}, Device: {}, Name: {}".format(info.context["client"].user, device, name))
        
        try: 
            db.delete_device_property(device, name)
            log = DeleteDevicePropertyUserAction(
                                            timestamp = datetime.now(), 
                                            user = info.context["client"].user,
                                            device = device,
                                            name = name
                                        )
            user_actions.put(log)

            return DeleteDeviceProperty(ok=True, message=["Success"])
        except (PyTango.DevFailed, PyTango.ConnectionFailed,
                PyTango.CommunicationFailed, PyTango.DeviceUnlocked) as error:
            e = error.args[0]
            return DeleteDeviceProperty(ok=False, message=[e.desc, e.reason])
        except Exception as e:
            return DeleteDeviceProperty(ok=False, message=[str(e)])
        
class Mutations(ObjectType):
    """This class contains all the mutations."""

    put_device_property = PutDeviceProperty.Field()
    delete_device_property = DeleteDeviceProperty.Field()
    setAttributeValue = SetAttributeValue.Field()
    execute_command = ExecuteDeviceCommand.Field()

