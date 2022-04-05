# -*- coding: utf-8 -*-
"""
OpenPMU - PMU/ADC Interface
Copyright (C) 2022  www.OpenPMU.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

UDP server used to receive data.
Data is received in an xml file format and parsed to a dict as:

.. code:: python

    {
        Fs:int,
        Frame:int,
        n:int,
        Bits:int,
        Channels:int,
        Date:str,
        Time:str with microsecond,
        Channel_0:
        {
            Name:str,
            Type:str,
            Phase:str,
            Range:str,
            Payload:list,
        }
    Channel_1:{...},
    .,
    .,
    .,
    }

see :ref:`xml-exchange-format`

Changes 2022-02-14
* Added   - "PayloadRAW" key for RAW ADC sampled values (SV)
* Added   - UDP Multicast support
* Removed - Legace print function
"""
import socket, base64
import numpy as np
from lxml import etree
import struct

__author__ = 'Xiaodong, OpenPMU.org'


class Receiver:
    """
    A PMU Cape XML format receiver
    """

    CH_NUMBER = 8  # max ch number
    ADC_MAX_VALUE = 2 ** 15-1  # ADC max sampled value, for 16 bit ADC
    ADC_RANGE = 5.0  # ADC input voltage range, should be 5 or 10 V

    def __init__(self, ip, port, forward, forwardIP='', forwardPort=0):
        # socket used to receive data
        
        if self.MCcheck(ip):
            # Multicast port
            self.socketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socketIn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socketIn.bind(('', port))
            mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
            self.socketIn.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            self.socketIn.settimeout(1)                         # Timeout 1 second
        else:
            # Normal UDP port
            self.socketIn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socketIn.bind((ip, port))
        
        # socket used to forward data to another port
        self.forward = forward
        self.forwardIP = forwardIP
        self.forwardPort = forwardPort
        if forward:
            self.socketOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # store parsed xml information
        self.xmlInfo = dict()
        # covert data in xml to different types based on tag name
        self.xmlTypeConvert = lambda tag: {  # 'Date': lambda x: datetime.strptime(x, "%Y-%m-%d").date(),
            # 'Time': lambda x: datetime.strptime(x, "%H:%M:%S.%f").time(),
            'Frame': int,
            'Fs': int,
            'n': int,
            'bits': int,
            'Channels': int,
            'Payload': self.payloadConvert,
            'PayloadRAW': self.payloadConvertRAW 
        }.get(tag, lambda x: x)

    def MCcheck(self, ip):
        """
        Checks if 'ip' is in multicast range
        """
        
        if int(ip.split(".")[0]) in range(224,240):
            return True
        else:
            return False

    def close(self):
        """
        Close the connection with PMU
        """

        self.socketIn.close()

    def __del__(self):
        self.close()
        
        
    # convert from base64 to  np.array
    def payloadConvert(self, payloadBase64):
        return np.frombuffer(bytearray(base64.standard_b64decode(payloadBase64)), dtype='>i2')/float(Receiver.ADC_MAX_VALUE) * Receiver.ADC_RANGE#big endian

    # convert from base64 to  np.array
    def payloadConvertRAW(self, payloadBase64):
        return np.frombuffer(bytearray(base64.standard_b64decode(payloadBase64)), dtype='>i2') #big endian

    def receive(self, timeout=1):
        """
        Receive data from client.
        If forward is true, then data forwarded to another address.

        :param timeout: max waiting time for xml data, in seconds
        :return: received data in a python dict
        """

        self.socketIn.settimeout(timeout)  # in seconds
        try:
            xml, __address = self.socketIn.recvfrom(8192)
        except socket.timeout:
            return
        if self.forward:
            self.socketOut.sendto(xml, (self.forwardIP, self.forwardPort))

        # parse the received data and store it in a dict
        level0 = etree.fromstring(xml)
        try:
            for level1 in list(level0):
                text = level1.text
                tag = level1.tag
                if tag.startswith("Channel_"):
                    self.xmlInfo[tag] = dict()
                    for level2 in list(level1):
                        if level2.tag == "Payload":     # Create new key to store RAW ADC sampled values (SV)
                            self.xmlInfo[tag]["PayloadRAW"] = self.xmlTypeConvert("PayloadRAW")(level2.text)  
                        self.xmlInfo[tag][level2.tag] = self.xmlTypeConvert(level2.tag)(level2.text)
                else:
                    self.xmlInfo[tag] = self.xmlTypeConvert(tag)(text)

        except AttributeError as e:
            print("Error occurred while parsing xml information")
            print(e)
            return None
        else:
            return self.xmlInfo
