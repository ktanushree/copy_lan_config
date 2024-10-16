#!/usr/bin/env python

"""
Script to copy VLAN interfaces (SVIs or Subinterfaces) that are used for LAN from one ION to the other
Author: tkamath@paloaltonetworks.com
Version: 1.0.0b1
"""

##############################################################################
# Import Libraries
##############################################################################
import prisma_sase
import argparse
import sys

##############################################################################
# Prisma SD-WAN Auth Token
##############################################################################
try:
    from prismasase_settings import PRISMASASE_CLIENT_ID, PRISMASASE_CLIENT_SECRET, PRISMASASE_TSG_ID

except ImportError:
    PRISMASASE_CLIENT_ID=None
    PRISMASASE_CLIENT_SECRET=None
    PRISMASASE_TSG_ID=None


#############################################################################
# Global Variables
#############################################################################
elem_id_name = {}
elem_name_id = {}
elemid_siteid = {}
elem_id_model = {}

DELETE_ATTR_POST = ["id", "_etag", "_schema", "_created_on_utc", "_updated_on_utc", "_content_length", "_status_code", "_request_id"]

def create_dicts(sase_session):
    #
    # Elements
    #
    resp = sase_session.get.elements()
    if resp.cgx_status:
        elemlist = resp.cgx_content.get("items", None)

        for elem in elemlist:
            elem_id_name[elem["id"]] = elem["name"]
            elem_name_id[elem["name"]] = elem["id"]
            elemid_siteid[elem["id"]] = elem["site_id"]
            elem_id_model[elem["id"]] = elem["model_name"]
    else:
        print("ERR: Could not retrieve elements")
        prisma_sase.jd_detailed(resp)

    return


def go():
    #############################################################################
    # Begin Script
    #############################################################################
    parser = argparse.ArgumentParser(description="{0}.".format("Prisma SD-WAN Port Speed Config Details"))
    config_group = parser.add_argument_group('Config', 'Details for the ION devices you wish to update')
    config_group.add_argument("--src_element", "-S", help="Source Element Name", default=None)
    config_group.add_argument("--dst_element", "-D", help="Destination Element Name",default=None)
    config_group.add_argument("--parent_interface", "-P", help="Parent Interface Name",default=None)

    #############################################################################
    # Parse Arguments
    #############################################################################
    args = vars(parser.parse_args())

    src_element = args.get("src_element", None)
    if src_element is None:
        print("ERR: Invalid Source Element Name. Please provide a valid Element Name")
        sys.exit()

    dst_element = args.get("dst_element", None)
    if dst_element is None:
        print("ERR: Invalid Destination Element Name. Please provide a valid Element Name")
        sys.exit()

    parent_interface = args.get("parent_interface", None)
    if parent_interface is None:
        print("ERR: Invalid Parent Interface Name. Please provide a valid Interface Name")
        sys.exit()

    ##############################################################################
    # Login
    ##############################################################################
    sase_session = prisma_sase.API()
    sase_session.interactive.login_secret(client_id=PRISMASASE_CLIENT_ID,
                                          client_secret=PRISMASASE_CLIENT_SECRET,
                                          tsg_id=PRISMASASE_TSG_ID)
    if sase_session.tenant_id is None:
        print("ERR: Login Failure. Please provide a valid Service Account")
        sys.exit()
    ##############################################################################
    # Create Translation Dicts
    ##############################################################################
    print("Building Translation Dicts")
    create_dicts(sase_session=sase_session)
    ##############################################################################
    # Validate Element Name
    ##############################################################################
    if src_element not in elem_name_id.keys():
        print("ERR: Element {} not found! Please provide a valid name".format(src_element))
        sys.exit()

    if dst_element not in elem_name_id.keys():
        print("ERR: Element {} not found! Please provide a valid name".format(dst_element))
        sys.exit()
    ##############################################################################
    # Retrieve Interfaces from Source Device
    ##############################################################################
    src_eid = elem_name_id[src_element]
    src_sid = elemid_siteid[src_eid]
    src_ion_model = elem_id_model[src_eid]

    dst_eid = elem_name_id[dst_element]
    dst_sid = elemid_siteid[dst_eid]
    dst_parent_id = None
    dst_vlan_names = []
    dst_intfname_intf = {}
    src_interface_type="vlan"
    if src_ion_model in ["1200", "3200", "5200", "9200", "3102v", "3104v", "3108v"]:
        src_interface_type="subinterface"

    ##############################################################################
    # Retrieve Parent Interface ID for Dest Element
    ##############################################################################
    dest_interfaces = []
    resp = sase_session.get.interfaces(site_id=dst_sid, element_id=dst_eid)
    if resp.cgx_status:
        dest_interfaces = resp.cgx_content.get("items", None)
        for intf in dest_interfaces:
            if intf["name"] == parent_interface:
                dst_parent_id = intf["id"]

            if intf["used_for"] == "lan":
                dst_vlan_names.append(intf["name"])
                dst_intfname_intf[intf["name"]] = intf
    else:
        print("ERR: Could not get interfaces from {}".format(dst_element))
        prisma_sase.jd_detailed(resp)

    ##############################################################################
    # Retrieve Interfaces from Source Element
    ##############################################################################
    print("Retrieving Interfaces: {}".format(src_element))
    source_interfaces = []
    resp = sase_session.get.interfaces(site_id=src_sid, element_id=src_eid)
    if resp.cgx_status:
        source_interfaces = resp.cgx_content.get("items", None)
    else:
        print("ERR: Could not retrieve interfaces")
        prisma_sase.jd_detailed(resp)

    ##############################################################################
    # Configures VLAN interfaces on Destination Element - Subinterface
    ##############################################################################
    print("Configuring Interface: {}".format(dst_element))
    if src_interface_type == "subinterface":
        for intf in source_interfaces:
            if intf["type"] == src_interface_type:
                if intf["used_for"] == "lan":
                    ##############################################################################
                    # If subinterface exists, update config
                    ##############################################################################
                    if intf["name"] in dst_vlan_names:
                        print("\t{} already configured!".format(intf["name"]))

                        dst_payload = dst_intfname_intf[intf["name"]]
                        for item in intf.keys():
                            if item not in DELETE_ATTR_POST:
                                dst_payload[item] = intf[item]

                        resp = sase_session.put.interfaces(site_id=dst_sid,
                                                           element_id=dst_eid,
                                                           interface_id=dst_payload["id"],
                                                           data=dst_payload)
                        if resp.cgx_status:
                            print("\t{} Updated".format(intf["name"], dst_element))

                        else:
                            print("ERR: Could not update interface {}".format(intf["name"]))
                            prisma_sase.jd_detailed(resp)
                    ##############################################################################
                    # Else, create new subinterface
                    ##############################################################################
                    else:
                        dst_payload = {}
                        for item in intf.keys():
                            if item not in DELETE_ATTR_POST:
                                dst_payload[item] = intf[item]

                        dst_payload["parent"] = dst_parent_id
                        resp = sase_session.post.interfaces(site_id=dst_sid, element_id=dst_eid, data=dst_payload)
                        if resp.cgx_status:
                            print("\t{} Created".format(intf["name"], dst_element))

                        else:
                            print("ERR: Could not create interface {}".format(intf["name"]))
                            prisma_sase.jd_detailed(resp)
    ##############################################################################
    # Configures VLAN interfaces on Destination Element - SVI
    ##############################################################################
    else:
        source_parent = None
        for intf in source_interfaces:
            if intf["type"] == src_interface_type:
                if intf["used_for"] == "lan":
                    ##############################################################################
                    # If SVI exists, update config
                    ##############################################################################
                    if intf["name"] in dst_vlan_names:
                        dst_payload = dst_intfname_intf[intf["name"]]
                        for item in intf.keys():
                            if item not in DELETE_ATTR_POST:
                                dst_payload[item] = intf[item]

                        resp = sase_session.put.interfaces(site_id=dst_sid,
                                                           element_id=dst_eid,
                                                           interface_id=dst_payload["id"],
                                                           data=dst_payload)
                        if resp.cgx_status:
                            print("\t{} Updated".format(intf["name"], dst_element))

                        else:
                            print("ERR: Could not update interface {}".format(intf["name"]))
                            prisma_sase.jd_detailed(resp)

                    ##############################################################################
                    # Else, create new SVI interface
                    ##############################################################################
                    else:
                        dst_payload = {}
                        for item in intf.keys():
                            if item not in DELETE_ATTR_POST:
                                dst_payload[item] = intf[item]

                        resp = sase_session.post.interfaces(site_id=dst_sid, element_id=dst_eid, data=dst_payload)
                        if resp.cgx_status:
                            print("\t{} Created".format(intf["name"], dst_element))

                        else:
                            print("ERR: Could not create interface {}".format(intf["name"]))
                            prisma_sase.jd_detailed(resp)

            if intf["name"] == parent_interface:
                source_parent = intf

        ##############################################################################
        # If SVI, update parent port with trunk VLANs
        ##############################################################################
        print("Updating Parent Interface trunk VLANs on {}".format(dst_element))
        for intf in dest_interfaces:
            if intf["name"] == parent_interface:

                for item in source_parent.keys():
                    if item not in DELETE_ATTR_POST:
                        intf[item] = source_parent[item]

                resp = sase_session.put.interfaces(site_id=dst_sid,
                                                   element_id=dst_eid,
                                                   interface_id=intf["id"],
                                                   data=intf)
                if resp.cgx_status:
                    print("\t{} Updated".format(intf["name"], dst_element))

                else:
                    print("ERR: Could not update interface {}".format(intf["name"]))
                    prisma_sase.jd_detailed(resp)

    return

if __name__ == "__main__":
    go()