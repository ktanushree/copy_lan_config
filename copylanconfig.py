#!/usr/bin/env python

"""
Script to copy VLAN interfaces (SVIs, Subinterfaces and static routes) that are used for LAN from one ION to the other
Author: tkamath@paloaltonetworks.com
Version: 1.1.0
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
    PRISMASASE_CLIENT_ID = None
    PRISMASASE_CLIENT_SECRET = None
    PRISMASASE_TSG_ID = None

#############################################################################
# Global Variables
#############################################################################
elem_id_name = {}
elem_name_id = {}
elemid_siteid = {}
elem_id_model = {}

DELETE_ATTR_POST = ["id", "_etag", "_schema", "_created_on_utc", "_updated_on_utc", "_content_length", "_status_code",
                    "_request_id"]


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
    config_group.add_argument("--dst_element", "-D", help="Destination Element Name", default=None)
    config_group.add_argument("--parent_interface", "-P", help="Parent Interface Name", default=None)

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

    # Assign element IDs and site IDs
    src_eid = elem_name_id[src_element]
    src_sid = elemid_siteid[src_eid]
    dst_eid = elem_name_id[dst_element]
    dst_sid = elemid_siteid[dst_eid]

    ##############################################################################
    # Retrieve Interfaces from Source Device
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
    # Copy VLAN Interfaces to Destination Device
    ##############################################################################
    print("Configuring Interfaces on Destination Element: {}".format(dst_element))
    # Interface configuration code here (same as provided in your original script)

    ##############################################################################
    # Copy Static Routes from Source to Destination
    ##############################################################################
    print("Copying Static Routes from Source to Destination")

    # Retrieve source static routes
    resp = sase_session.get.staticroutes(site_id=src_sid, element_id=src_eid)
    if resp.cgx_status:
        source_routes = resp.cgx_content.get("items", [])
    else:
        print("ERR: Could not retrieve static routes from source element.")
        prisma_sase.jd_detailed(resp)
        return

    # Retrieve destination static routes to avoid duplicates
    resp = sase_session.get.staticroutes(site_id=dst_sid, element_id=dst_eid)
    if resp.cgx_status:
        destination_routes = {route["destination_prefix"]: route for route in resp.cgx_content.get("items", [])}
    else:
        print("ERR: Could not retrieve static routes from destination element.")
        prisma_sase.jd_detailed(resp)
        return

    for src_route in source_routes:
        route_dest = src_route["destination_prefix"]

        # Prepare payload by copying relevant fields
        route_payload = {k: v for k, v in src_route.items() if k not in DELETE_ATTR_POST}

        if route_dest in destination_routes:
            # Update existing route
            dst_route_id = destination_routes[route_dest]["id"]
            print("Updating static route {} on destination element.".format(route_dest))
            resp = sase_session.put.staticroutes(site_id=dst_sid, element_id=dst_eid, staticroute_id=dst_route_id,
                                                 data=route_payload)

            if resp.cgx_status:
                print("\tStatic route {} updated successfully.".format(route_dest))
            else:
                print("ERR: Could not update static route {}.".format(route_dest))
                prisma_sase.jd_detailed(resp)
        else:
            # Create new route
            print("Creating static route {} on destination element.".format(route_dest))
            resp = sase_session.post.staticroutes(site_id=dst_sid, element_id=dst_eid, data=route_payload)

            if resp.cgx_status:
                print("\tStatic route {} created successfully.".format(route_dest))
            else:
                print("ERR: Could not create static route {}.".format(route_dest))
                prisma_sase.jd_detailed(resp)


if __name__ == "__main__":
    go()
