"""
This work is licensed under a Creative Commons Attribution 4.0 International License http://creativecommons.org/licenses/by/4.0/ 
Credits to Michael Niehaus as it is heavly based on AutopilotUtility https://www.powershellgallery.com/packages/AutopilotUtility
"""

import base64, struct,json, binascii
import uuid

class Version:
    def __init__(self, major, minor, build, rev):
        self.major = major
        self.minor = minor
        self.build = build
        self.rev = rev

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.build}.{self.rev}"

    def toJSON(self):
        return json.dumps(self.__dict__)

def convert_from_autopilot_hash(CSVFile=None, Hash=None):
    results = []
    if CSVFile:
        with open(CSVFile, 'r') as f:
            csvContents = [line.strip().split(',') for line in f.readlines()]
            hashes = [row[0] for row in csvContents[1:]] # skip header
    elif Hash:
        hashes = [Hash]
    else:
        results.append({"Hash": "?", "Error": "Hash must be provided"})
        return results

    value_type_utf8string = {
        13: "TpmVersion",
        14: "SmbiosSerial",
        15: "SmbiosFirmwareVendor",
        16: "SmbiosSystemManufacturer",
        17: "SmbiosProductName",
        18: "SmbiosSKUNumber",
        19: "SmbiosSystemFamily",
        20: "SmbiosFirmwareVendor2",
        21: "SmbiosBoardProduct",
        22: "SmbiosBoardVersion",
        23: "SmbiosSystemVersion",
        24: "ProductKeyID",
        26: "ProductKeyPkPn",
        28: "DiskSSNKernel",
    }

    value_type_PowerPlatformRole = {
        0: "Unspecified",
        1: "Desktop",
        2: "Mobile",
        3: "Workstation",
        4: "EnterpriseServer",
        5: "SOHOServer",
        6: "AppliancePC",
        7: "PerformanceServer",
        8: "Slate",
        9: "Maximum",

    }

    
    for h in hashes:
        try:
            binary = base64.b64decode(h)
        except binascii.Error:
            results.append({"Hash": h, "Error": "Invalid hash"})
            return results


        # Validate the header
        if binary[0] != 79 or binary[1] != 65:
            results.append({"Hash": h, "Error": "Invalid hash header"})
            return results

        # Validate the checksum
        # TODO

        # Process the values
        totalLength = struct.unpack('<H', binary[2:4])[0]
        data = {}
        currentOffset = 4
        diskSerialCount = 0
        diskInfoCount = 0
        displayResolutionCount = 0
        gpuCount = 0
        gpuNameCount = 0
        networkCount = 0
        while currentOffset < totalLength:
            valueType = binary[currentOffset]
            #length = struct.unpack('<H', binary[currentOffset+2:currentOffset+4])[0]
            length = struct.unpack_from('<H', binary, currentOffset + 2)[0]
            if valueType == 1:
                offset = currentOffset + 4
                # Two version strings, 8 bytes each
                versions = []
                for i in range(2):
                    minor = int.from_bytes(binary[offset:offset+2], byteorder='little')
                    major = int.from_bytes(binary[offset+2:offset+4], byteorder='little')
                    rev = int.from_bytes(binary[offset+4:offset+6], byteorder='little')
                    build = int.from_bytes(binary[offset+6:offset+8], byteorder='little')
                    offset += 8
                    versions.append(Version(major, minor, build, rev))
                data["ToolBuild"] = versions[0].__str__()
                data["OSBuild"] = versions[1].__str__()
                # Need to figure out the next five bytes
                # Last three bytes
                if binary[currentOffset + length - 3] == 2:
                    data["OSType"] = "FullOS"
                else:
                    data["OSType"] = binary[currentOffset + length - 3]
                if binary[currentOffset + length - 2] == 0:
                    data["OSCpuArchitecture"] = "X86"
                elif binary[currentOffset + length - 2] == 9:
                    data["OSCpuArchitecture"] = "X64"
                elif binary[currentOffset + length - 2] == 12:
                    data["OSCpuArchitecture"] = "ARM64"
                else:
                    data["OSCpuArchitecture"] = binary[currentOffset + length - 2]
                data["ToolVersion"] = binary[currentOffset + length - 1]
            elif valueType == 2:
                if binary[currentOffset + 4] == 0:
                    data["ProcessorArchitecture"] = "X86"
                elif binary[currentOffset + 4] == 9:
                    data["ProcessorArchitecture"] = "X64"
                elif binary[currentOffset + 4] == 12:
                    data["ProcessorArchitecture"] = "ARM64"
                else:
                    data["ProcessorArchitecture"] = binary[currentOffset + 4]
                data["ProcessorPackages"] = int.from_bytes(binary[currentOffset + 6:currentOffset + 8], byteorder='little')
                data["ProcessorCores"] = int.from_bytes(binary[currentOffset + 8:currentOffset + 10], byteorder='little')
                data["ProcessorThreads"] = int.from_bytes(binary[currentOffset + 10:currentOffset + 12], byteorder='little')
                if binary[currentOffset + 12] == 1:
                    data["ProcessorHyperthreading"] = True
                else:
                    data["ProcessorHyperthreading"] = False
            elif valueType == 3:
                data["ProcessorManufacturer"] = str(binary[currentOffset + 4 : currentOffset + length - 6], 'utf-8')
            elif valueType == 4:
                data["ProcessorModel"] = str(binary[currentOffset + 4 : currentOffset + length - 6], 'utf-8')
            elif valueType == 5:
                data["TotalPhysicalRam"] = int.from_bytes(binary[currentOffset + 4:currentOffset + 6], byteorder="little")
                data["SmbiosRamMaximumCapacity"] = int.from_bytes(binary[currentOffset + 12:currentOffset + 14], byteorder="little")
                data["SmbiosRamSlots"] = int.from_bytes(binary[currentOffset + 20:currentOffset + 22], byteorder="little")
                data["SmbiosRamArrayCount"] = int.from_bytes(binary[currentOffset + 22:currentOffset + 24], byteorder="little")
                error_correction = binary[currentOffset + 24]
                if error_correction == 3:
                    data["SmbiosRamErrorCorrection"] = "None"
                elif error_correction == 4:
                    data["SmbiosRamErrorCorrection"] = "Parity"
                elif error_correction == 5:
                    data["SmbiosRamErrorCorrection"] = "Single-bit ECC"
                elif error_correction == 6:
                    data["SmbiosRamErrorCorrection"] = "Multi-bit ECC"
                elif error_correction == 7:
                    data["SmbiosRamErrorCorrection"] = "CRC"
                else:
                    data["SmbiosRamErrorCorrection"] = error_correction
            elif valueType == 6:
                diskInfoCount += 1
                data[f"Disk{diskInfoCount}.DiskCapacity"] = int.from_bytes(binary[currentOffset + 4:currentOffset + 8], byteorder="little")
                bus_type = binary[currentOffset + 12]
                if bus_type == 1:
                    busType = "SCSI"
                elif bus_type == 2:
                    busType = "ATAPI"
                elif bus_type == 3:
                    busType = "ATA"
                elif bus_type == 8:
                    busType = "RAID"
                elif bus_type == 10:
                    busType = "SAS"
                elif bus_type == 11:
                    busType = "SATA"
                elif bus_type == 17:
                    busType = "NVMe"
                else:
                    busType = bus_type
                data[f"Disk{diskInfoCount}.StorageBusType"] = busType
                if busType == "NVMe":
                    data[f"Disk{diskInfoCount}.DiskType"] = "NVMe"
                else:
                    disk_type = binary[currentOffset + 14]
                    if disk_type == 0:
                        data[f"Disk{diskInfoCount}.DiskType"] = "SSD"
                    elif disk_type == 255:
                        data[f"Disk{diskInfoCount}.DiskType"] = "HDD"
            elif valueType == 7:
                diskSerialCount += 1
                data[f"Disk{diskSerialCount}.DiskSerial"] = str(binary[currentOffset + 4 : currentOffset + length], 'utf-8')
            elif valueType == 8:
                networkCount += 1
                medium = binary[currentOffset + 4]
                if medium == 1:
                    medium = "Wireless Lan"
                elif medium == 9:
                    medium = "Native 802.11"
                elif medium == 10:
                    medium = "Bluetooth"
                elif medium == 14:
                    medium = "Ethernet"
                else:
                    medium = medium
                data[f"Network{networkCount}.PhysicalMedium"] = medium
                mac_bytes=bytes(binary[currentOffset +8 : currentOffset + 14])
                mac_address = binascii.hexlify(mac_bytes).decode('utf-8')
                formatted_mac_address = ':'.join([mac_address[i:i+2] for i in range(0, len(mac_address), 2)])
                data[f"Network{networkCount}.MacAddress"] = formatted_mac_address
            elif valueType == 9:
                displayResolutionCount += 1
                data[f"Display{displayResolutionCount}.SizePhysicalH"] = int.from_bytes(binary[currentOffset + 4:currentOffset + 6], byteorder='little')
                data[f"Display{displayResolutionCount}.SizePhysicalV"] = int.from_bytes(binary[currentOffset + 6:currentOffset + 8], byteorder='little')
                data[f"Display{displayResolutionCount}.ResolutionHorizontal"] = int.from_bytes(binary[currentOffset + 8:currentOffset + 10], byteorder='little')
                data[f"Display{displayResolutionCount}.ResolutionVertical"] = int.from_bytes(binary[currentOffset + 10:currentOffset + 12], byteorder='little')
            elif valueType == 10:
                data["ChassisType"] = binary[currentOffset + 4]
                #TODO: Add more chassis types
                data["PowerPlatformRole"] = value_type_PowerPlatformRole[binary[currentOffset + 5]]
            elif valueType == 11:
                data["OfflineDeviceId"] = base64.b64encode(binary[currentOffset + 14 : currentOffset + length - 1]).decode()
                if binary[currentOffset + 8] == 1:
                    data["OfficeDeviceIdType"] = "TPM_EK"
                elif binary[currentOffset + 8] == 2:
                    data["OfficeDeviceIdType"] = "UEFI_VARIABLE_TPM"
                else:
                    data["OfficeDeviceIdType"] = binary[currentOffset + 8]
            elif valueType == 12:
                guid_bytes = bytes(binary[currentOffset + 4 : currentOffset + length])
                smbiosguid = uuid.UUID(bytes=guid_bytes).urn.replace("urn:uuid:", "")
                data["SmbiosUuid"] = smbiosguid
            elif valueType in value_type_utf8string:
                key = value_type_utf8string[valueType]
                data[key] = str(binary[currentOffset + 4 : currentOffset + length - 1], 'utf-8')
            elif valueType == 25:
                data["TpmEkPub"] = str(base64.b64encode(binary[currentOffset + 4 : currentOffset + length - 1]), 'utf-8')
            elif valueType == 27:
                #someint = (int.from_bytes(binary[currentOffset + 4 : currentOffset + length - 1], byteorder='little'))
                #print(someint)
                # We don't know what this is
                pass
            elif valueType == 29:
                gpuCount += 1
                data["Gpu%d.DedicatedVideoMemory" % gpuCount] = int.from_bytes(binary[currentOffset + 4 : currentOffset + 8], byteorder='little')
                data["Gpu%d.DedicatedSystemMemory" % gpuCount] = int.from_bytes(binary[currentOffset + 8 : currentOffset + 12], byteorder='little')
                # Not sure on these flags, likely the last two bytes:
            elif valueType == 30:
                gpuNameCount += 1
                data[f"Gpu{gpuNameCount}.VideoAdapter"] = str(binary[currentOffset + 4 : currentOffset + length].decode("utf-16"))
            else:
                hex = ''.join('{:02x}'.format(b) for b in binary[currentOffset:currentOffset + length])
                print(f"@ {currentOffset} : {valueType} ( {length} ) {hex}")
                #print(f"@ {currentOffset} : {valueType} ( {length} )")
            currentOffset += length
        results.append(data)
    return results