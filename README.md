# CNC_GRBL_Control

Python script to control a GRBL based CNC 3018 router. 
Features:
1. Adjust the Z axis, using a conductive plate and probe contacts. When milling a PCB, this is useful to locate 
the lowest point by connecting wires to probe pins of the CNC router to milling tool and the PCB.
When the tool touches the PCB, an electrical contact will be made.
2. Move the router head by X, Y and Z axis
3. Use limit switches to go to HOME position.
4. Stream a G-code file.
5. Activate/de-activate laser if any.
