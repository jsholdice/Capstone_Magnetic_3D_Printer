import csv
import time
import RPi.GPIO as GPIO

def main():
    # specify user path and run file 
    file_path = 'C:\\Users\\Jackson\\Dropbox\\My PC (DESKTOP-STTTK1A)\\Documents\\3H03\\Grabber.csv'
    # standard time in papers to achieve magnetic particle reorientation under applied magnetic field [s]
    magnetization_delay = 120
    # current time to cure one voxel completely, change accordingly based on UV LED irradiance
    curing_delay = 60

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
    dir_pin_p2 = 9
    dir_pin_n2 = 10
    pul_pin2 = 11
    pin_list.append([dir_pin_p2, dir_pin_n2, pul_pin2])

    #z motor
    dir_pin_p3 = 8
    dir_pin_n3 = 25
    pul_pin3 = 7
    pin_list.append([dir_pin_p3, dir_pin_n3, pul_pin3])

    #top magnet
    dir_pin_p4 = 19
    dir_pin_n4 = 13
    pul_pin4 = 26
    pin_list.append([dir_pin_p4, dir_pin_n4, pul_pin4])

    #bottom magnet
    dir_pin_p5 = 15
    dir_pin_n5 = 14
    pul_pin5 = 18
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
        
        # iterate through each row containing the data for each voxel
        for row in csv_reader:
            # for each voxel iterate over the steps assigned to each motor in order of x,y,z,top,bottom 
            for index, current_steps in enumerate(row):
                # calculate number of steps required to move from previous position to current position
                motor_steps = int(current_steps) - previous_steps[index]

                if motor_steps > 0:
                    rotate(motor_steps, pin_list[index], 'Forward')
                elif motor_steps < 0:
                    rotate(motor_steps, pin_list[index], 'Backward')

                # execute after moving all motors for specific voxel
                if index == len(row) - 1:
                    # allow time for magnetix particles to reorientate in resin 
                    time.sleep(magnetization_delay)
                    # turn on UV LED pin
                    GPIO.output(pin_list[index + 1], GPIO.HIGH)
                    # allow time for UV LED to cure resin 
                    time.sleep(curing_delay)
                
                previous_steps[index] = int(current_steps)


def rotate(steps, motor_pins, direction):
    delay = 0.01
    print(steps)
    
    p_dir_pin = motor_pins[0]
    n_dir_pin = motor_pins[1]
    pul_pin = motor_pins[2]

    if direction == 'Forward':
        GPIO.output(p_dir_pin, GPIO.HIGH)
        GPIO.output(n_dir_pin, GPIO.LOW)
    elif direction == 'Backward':
        GPIO.output(p_dir_pin, GPIO.LOW)
        GPIO.output(n_dir_pin, GPIO.HIGH)
    
    for _ in range(steps):
        GPIO.output(pul_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(pul_pin, GPIO.LOW)
        time.sleep(delay)

if __name__ == "__main__":
    main()