#!/usr/bin/env python3
import os
from pathlib import Path
import sys

__projectdir__ = Path(os.path.dirname(os.path.realpath(__file__)) + '/')

import collections

def batteryinfo_single(batteries = None):
    """
    Just use acpi if no batteries specified.
    Otherwise, directly read /sys/class/power_supply/BAT
    """
    import subprocess

    output = subprocess.check_output(['acpi', '-b']).decode('latin-1')[:-1]
    percent = int(output.split(',')[1].strip('%').strip(' '))

    temp = output.split(',')[0].split(' ')[2]
    if temp == 'Discharging':
        charging = False
    else:
        charging = True

    if len(output.split(',')) > 2:
        timeremaining = output.split(',')[2].split(' ')[1]
    else:
        timeremaining = None

    return(charging, percent, timeremaining)


def batteryinfo_multiple(batteries = None):
    # get batteries in /sys/class/power_supply if not defined
    if batteries is None:
        batteries = os.listdir('/sys/class/power_supply')
        batteries = [battery for battery in batteries if battery.startswith('BAT')]
        batteries = sorted(batteries)

    
    batterydict = collections.OrderedDict()
    for battery in batteries:
        batterydict[battery] = {}

        # get energy_full and energy_now
        # for BAT1 I found that energy_full was empty so read energy_full_design if there's a problem instead
        try:
            with open(os.path.join('/sys/class/power_supply', battery, 'energy_full')) as f:
                batterydict[battery]['energy_full'] = int(f.read()[: -1])
        except Exception:
            with open(os.path.join('/sys/class/power_supply', battery, 'energy_full_design')) as f:
                batterydict[battery]['energy_full'] = int(f.read()[: -1])
        with open(os.path.join('/sys/class/power_supply', battery, 'energy_now')) as f:
            batterydict[battery]['energy_now'] = int(f.read()[: -1])
        with open(os.path.join('/sys/class/power_supply', battery, 'power_now')) as f:
            batterydict[battery]['power_now'] = int(f.read()[: -1])
        with open(os.path.join('/sys/class/power_supply', battery, 'status')) as f:
            batterydict[battery]['status'] = f.read()[: -1]
        
        batterydict[battery]['stringdetails'] = 'Battery: ' + battery + '. Energy: ' + str(round((batterydict[battery]['energy_now']/1000000), 1)) + '/' + str(round((batterydict[battery]['energy_full']/1000000), 1)) + ' (' + str(round(batterydict[battery]['energy_now'] / batterydict[battery]['energy_full'] * 100, 1)) + '%) + Status: ' + batterydict[battery]['status'] + '.'

    return(batterydict)

    

# New Call:{{{1
def batterycheck_single(percentmin, charging, percent, timeremaining):
    """
    Run genpopup_test for a given percentage.
    """
    
    if not os.path.isdir('/tmp/linux-battery-info/'):
        os.mkdir('/tmp/linux-battery-info/')

    if percent <= percentmin and charging is False:
        test = True
        message = 'Battery discharging. Currently at ' + str(percent) + '%. Remaining time: ' + timeremaining
    else:
        test = False
        message = None
            
    sys.path.append(str(__projectdir__ / Path('submodules/linux-popupinfo/')))
    from displaypopup_func import genpopup
    # genpopup(message, title = 'Battery')

    sys.path.append(str(__projectdir__ / Path('submodules/linux-popupinfo/')))
    from displaypopup_func import genpopup_test
    genpopup_test(message, title = 'Battery', test = test, testnewlytrue = True, savefile = '/tmp/linux-battery-info/' + str(percentmin) + '.txt')


def batterycheck_multiple(percentmin, batterydict):
    if not os.path.isdir('/tmp/linux-battery-info/'):
        os.mkdir('/tmp/linux-battery-info/')

    # calculate overall percent
    energy_full_total = 0
    energy_full_now = 0
    discharging = False
    for battery in batterydict:
        energy_full_total = energy_full_total + batterydict[battery]['energy_full']
        energy_full_now = energy_full_now + batterydict[battery]['energy_now']
        if batterydict[battery]['status'] == 'Discharging':
            discharging = True
    percent = round((energy_full_now / energy_full_total * 100), 1)

    if percent <= percentmin and discharging is True:
        test = True
        message = 'Batteries discharging. Currently at ' + str(percent) + '%.\n\n' + '\n'.join([batterydict[battery]['stringdetails'] for battery in batterydict])
    else:
        test = False
        message = None
            
    sys.path.append(str(__projectdir__ / Path('submodules/linux-popupinfo/')))
    from displaypopup_func import genpopup_test
    genpopup_test(message, title = 'Battery', test = test, testnewlytrue = True, savefile = '/tmp/linux-battery-info/' + str(percentmin) + '.txt')


def allbattery(multiplebatteries = False, batteries = None):
    """
    Now run generally.
    """

    def batterycheck2(percentlt):
        if multiplebatteries is False and batteries is None:
            charging, percent, timeremaining = batteryinfo_single()
            ret = batterycheck_single(percentlt, charging, percent, timeremaining)
        else:
            batterydict = batteryinfo_multiple(batteries = batteries)
            ret = batterycheck_multiple(percentlt, batterydict)

    batterycheck2(90)
    batterycheck2(50)
    batterycheck2(10)


def allbattery_ap():
    #Argparse:{{{
    import argparse
    
    parser=argparse.ArgumentParser()
    parser.add_argument("--multiple", action = 'store_true')
    parser.add_argument("--batteries", nargs = '+', action = 'append')
    
    args=parser.parse_args()
    #End argparse:}}}

    allbattery(multiplebatteries = args.multiple, batteries = args.batteries)
