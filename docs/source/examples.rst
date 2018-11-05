Examples on query and mutation
==============================
Fetch information of devices
----------------------------

.. code:: python

    query{devices{ 
            name                # e.g. get the names of all devices
        }
    }  

    query{devices(pattern: "*tg_test*"){            #filter result with pattern
        name
        }
    }

Accessing attributes
--------------------

.. code:: python 

    query{
        devices(pattern: "sys/tg_test/1"){
            name,
            attributes {
                name,
                datatype,
                }
            }
        }

    query{
        devices(pattern: "sys/tg_test/1"){
        name,
        attributes(pattern: "*scalar*") {
                name,
                datatype,
                dataformat,
                label,
                unit,
                description,
                value,
                quality,
                timestamp
            }
            server{
            id,
            host
            }
        }
    }

Deleting device property
------------------------

.. code:: python 

    mutation{deleteDeviceProperty(device:"sys/tg_test/1", name: "Hej"){
            ok,
            message
        }
    }

Putting device property 
-----------------------

.. code:: python 

    mutation{putDeviceProperty(device:"sys/tg_test/1", name: "Hej", value: "test"){
            ok,
            message
        }
    }

Deleting device property
------------------------

.. code:: python 

    mutation{deleteDeviceProperty(device:"sys/tg_test/1",name:"Hej"){
            ok,
            message
        }
    } 

Setting value for an attribute
------------------------------ 

.. code:: python 

    mutation{SetAttributeValue(device:"sys/tg_test/1", name: "double_scalar",value: 2){
            ok,
            message
        }
    }
