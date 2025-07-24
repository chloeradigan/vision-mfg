from __future__ import absolute_import, division, print_function, unicode_literals
__metaclass__ = type

from cri_lib import CRIController
import time, collections

#from pocketnc_bridge import *

robotEvent = collections.namedtuple('robotEvent', ['openDoor','closeDoor','moveIn','moveOut', 'area_scan', 'camera_coord_capture'])

tasks = robotEvent
tasks.openDoor = 'LowReady.xml'
tasks.closeDoor = 'HighReady.xml'
tasks.moveIn = 'LowReady.xml'
tasks.moveOut = 'HighReady.xml'
tasks.cycle = 'cycles/1001.ngc'
tasks.camera_coord_capture = 'camera_coordinate_test.xml'
tasks.area_scan = r"C:\iRC-igusRobotControl-V14\Data\Programs\Area_Scan.xml"

class IgusBridge:
    def __init__(self, sim = True):
        self.sim = sim  
        self.controller = CRIController()
        self.connect()
    
    def connect(self):
        self.controller.connect("192.168.3.11")
        self.controller.set_active_control(True)

    def load_run_pgm(self, program_file):
        print("    Enabling Controller")
        self.enable_controller()
        time.sleep(5)
        print("    Loading Program: "+program_file)
        self.controller.load_programm(program_file)
        time.sleep(5)
        print("    Starting Program")
        self.controller.start_programm()
        time.sleep(300) 
        print("    Referencing all joints")
        self.controller.reference_all_joints()
        time.sleep(10)
        self.controller.disable()
        return True

    def enable_controller(self):
        self.controller.enable()
        self.controller.wait_for_kinematics_ready(10)

    def disable_controller(self):
        self.controller.disable()  
        time.sleep(5)

    def move_in(self, device, destination):
        print("Robot moving into device={}, dest={}".format(device, destination))
        return self.load_run_pgm(tasks.moveIn)

    def move_out(self, device, destination):
        print("Robot moving out of device={}, dest={}".format(device, destination))
        return self.load_run_pgm(tasks.moveOut)
    
    def open_door(self, device, destination):
        print("Robot opening the door of {}".format(device))    
        return self.load_run_pgm(tasks.openDoor)

    def close_door(self, device, destination):
        print("Robot closing the door of {}".format(device))
        return self.load_run_pgm(tasks.closeDoor)
    
    def r1_zero_ready(self, device, destination=""):
        print("Robot closing the door of {}".format(device))
        return self.load_run_pgm(tasks.r1_zero_ready)
    
    def camera_capture_coord(self, device, destination):
        print("Robot moving, camera capturing out of device={}, dest={}".format(device, destination))
        return self.load_run_pgm(tasks.camera_coord_capture)
    
    def area_scan(self, device):
        print("Robot running area scan")
        return self.load_run_pgm(tasks.area_scan)

if __name__ == "__main__":
    robot = IgusBridge(False)
    #pnc = PocketNCClient(False)
    robot.enable_controller()
    #robot.area_scan('r')
    robot.camera_capture_coord("r", "pnc")
    #robot.open_door("r","pnc")
    #robot.close_door("r","pnc")
    #print ("Running PocketNC Program: "+ tasks.cycle)
    #pnc.load_run_pgm(tasks.cycle)
    
