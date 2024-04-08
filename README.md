# Capstone_Magnetic_3D_Printer
This repo contains the two main programs used to operate the magnetic 3D printer for our capstone project. The purpose of this repo is to showcase the code developed throughout the project and the final results. 

### ComsolSlicer ###
* COMSOL was the Multiphysics platform used to simulate and test designs. A voxel is placed with the dimensions of the curing spot size and layer height. Each voxel is magnetized according to the desired torque under an applied magnetic field. The simulation is then saved as a Java file and this is the input into the ComsolSlicer.java program. 
* To operate the saved simulation java file name must replace Grabber_Dem_Real (Model model = Grabber_Demo_Real.run();). 
* Voxel geometric and magnetization data is obtained and converted to the required motor steps to achieve the orientation. Finally, the instruction set for the printer is outputted as a CSV file.

### Printer_Controller ###
* The generated CSV file is transferred to the Raspberry Pi and interpreted  by this Python program
* The Pi controls the motors and LED status by pulling desired pins to a high state.
* The motors are then positioned using the difference between their current and desired location.
* Ultimately, x-, y-, z-motors position a magnetic resin, then 2-rotational motors below magnetize the resin, and UV LED cures a specific voxel. This process is repeated until a 3D structure is created with unique local magnetizations, such that it deforms in a predetermined manner under an applied magnetic field. 


