# CNC_GRBL_Leveler

Python script to adjust the Z axis of a CNC router via UART, using a conductive plate and probe contacts.
When milling a PCB, this is useful to locate the lowest point by connecting wires to probe pins of the CNC router to milling tool and the PCB.
When the tool touches the PCB, an electrical contact will be made. 
