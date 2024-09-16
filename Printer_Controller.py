import csv
import time
import RPi.GPIO as GPIO


def main():
    # specify user path and run file 
    file_path = '/home/capstone/gm_code/triangle.csv'

    # standard time in papers to achieve magnetic particle reorientation under applied magnetic field [s]
    magnetization_delay = 2
    # current time to cure one voxel completely, change accordingly based on UV LED irradiance
    curing_delay = 10

    # set controllable pins on the R-Pi to motor driver pins
    pin_list = Pin_Initialization()
    # execute provided csv file containing GM Code
    GM_Code_Executor(file_path, pin_list, magnetization_delay, curing_delay)


def Pin_Initialization():
    # create nested list to store all motors respective motor driver pins
    pin_list = []

    #x motor
    dir_pin_p1 = 27
    dir_pin_n1 = 17
    pul_pin1 = 22
    pin_list.append([dir_pin_p1, dir_pin_n1, pul_pin1])

    #y motor
    dir_pin_p2 = 8
    dir_pin_n2 = 25
    pul_pin2 = 7
    pin_list.append([dir_pin_p2, dir_pin_n2, pul_pin2])

    #z motor
    dir_pin_p3 = 9
    dir_pin_n3 = 10
    pul_pin3 = 11
    pin_list.append([dir_pin_p3, dir_pin_n3, pul_pin3])

    #top magnet
    dir_pin_p4 = 20
    dir_pin_n4 = 16
    pul_pin4 = 21
    pin_list.append([dir_pin_p4, dir_pin_n4, pul_pin4])

    #bottom magnet
    dir_pin_p5 = 5
    dir_pin_n5 = 6
    pul_pin5 = 13
    pin_list.append([dir_pin_p5, dir_pin_n5, pul_pin5])

    # UV LED
    led_pin = 4
    pin_list.append([led_pin])

    # initialize all GPIO pins
    GPIO.setmode(GPIO.BCM)
    for sublist in pin_list:
        for pin in sublist:
            GPIO.setup(pin, GPIO.OUT)

    return pin_list


def GM_Code_Executor(file_path, pin_list, magnetization_delay, curing_delay):
    # open the provided GM code csv file 
    with open(file_path, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile)

        # initialize previous steps in a list of 0's the length of csv's row
        previous_steps = [0] * len(next(csv_reader))
        previous_motor_steps = [0] * len(previous_steps)
        switching_offset = [0, 0, 0, 0, 0]

        # iterate through each row containing the data for each voxel
        for row in csv_reader:
            # for each voxel iterate over the steps assigned to each motor in order of x,y,z,top,bottom 
            for index, current_steps in enumerate(row):
                
                # calculate number of steps required to move from previous position to current position
                motor_steps = int(current_steps) - previous_steps[index]             
                # determines which direction the motor should moved based on if it should rotate fwd or bckwd from it's current position
                if motor_steps > 0:
                    rotate(motor_steps, pin_list[index], 'Forward', previous_motor_steps[index], switching_offset[index])
                elif motor_steps < 0:
                    rotate(motor_steps, pin_list[index], 'Backward', previous_motor_steps[index], switching_offset[index])

                # delamination process after evry layer
                if index == 2 and motor_steps != 0:
                    rotate(motor_steps + 2000, pin_list[index], 'Forward', previous_motor_steps[index], switching_offset[index])
                    rotate(2000, pin_list[index], 'Backward', previous_motor_steps[index], switching_offset[index])
         
                # number of steps stated by the csv file 
                previous_steps[index] = int(current_steps)
                # number of steps the motor actually moved for previous voxel
                previous_motor_steps[index] = motor_steps
                
                # execute after moving all motors for specific voxel
                if index == len(row) - 1:
                    # allow time for magnetix particles to reorientate in resin 
                    time.sleep(magnetization_delay)
                    # turn on UV LED pin
                    GPIO.output(pin_list[index + 1], GPIO.HIGH)
                    # allow time for UV LED to cure resin 
                    time.sleep(curing_delay)
                    # turn off LED
                    GPIO.output(pin_list[index + 1], GPIO.LOW)

                    # return magnet to original position to apply neutral buyoancy field and prevent wire tanglement
                    if motor_steps < 0:
                        rotate(-motor_steps, pin_list[index], 'Forward', previous_motor_steps[index], switching_offset[index])
                    elif motor_steps > 0:
                        rotate(-motor_steps, pin_list[index], 'Backward', previous_motor_steps[index], switching_offset[index])
                    current_steps = 0
                
                # reset motor steps for last motor 
                if index == 4:  
                    previous_motor_steps[index] = -motor_steps      


# rotate motor given the number of steps and direction
def rotate(motor_steps, motor_pins, direction, previous_motor_steps, switch_step, delay=0.007):
    # set the pins for the desired motor
    p_dir_pin = motor_pins[0]
    n_dir_pin = motor_pins[1]
    pul_pin = motor_pins[2]

    # when motor switches direction add offset to account for switching steps
    if motor_steps * previous_motor_steps < 0:
        motor_steps = abs(motor_steps) + switch_step

    # initliaze direction pins
    if direction == 'Forward':
        GPIO.output(p_dir_pin, GPIO.HIGH)
        GPIO.output(n_dir_pin, GPIO.LOW)
    elif direction == 'Backward':
        GPIO.output(p_dir_pin, GPIO.LOW)
        GPIO.output(n_dir_pin, GPIO.HIGH)

    # rotate the motor by pulsing a square wave 
    for _ in range(abs(motor_steps)):
        GPIO.output(pul_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(pul_pin, GPIO.LOW)
        time.sleep(delay)

     
if __name__ == "__main__":
    main()
