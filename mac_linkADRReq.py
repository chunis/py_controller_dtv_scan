#!/usr/bin/python3

# Chunis Deng (chunchengfh@gmail.com)

import os
import sys

import grpc
from chirpstack_api_v3.ns.ns_pb2 import *
from chirpstack_api_v3.ns.ns_pb2_grpc import *


# Configuration.

# The API token (retrieved using the web-interface).
api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGlfa2V5X2lkIjoiYjk1MTJkMTUtNjM5YS00NzczLWI3MmEtYzg2MjkyOTBiNzAxIiwiYXVkIjoiYXMiLCJpc3MiOiJhcyIsIm5iZiI6MTY3NTQxMzI2OSwic3ViIjoiYXBpX2tleSJ9.VbPnONuIzCyT1tX_O7cigEP5xPbZaBj0Yt1XNHaTqG4"
auth_token = [("authorization", "Bearer %s" % api_token)]

def send_mac_command_linkadrreq(server, dev_eui, adr_list):
  # Connect without using TLS.
  channel = grpc.insecure_channel(server)
  client = NetworkServerServiceStub(channel)

  # Construct request.
  req = CreateMACCommandQueueItemRequest()
  req.dev_eui = dev_eui
  req.commands.append(bytes(adr_list))

  resp = client.CreateMACCommandQueueItem(req)


if __name__ == "__main__":
  #server = "localhost:8080"
  server = "192.168.1.210:8000"

  #dev_eui = "fefffffffdff0000"
  dev_eui = bytes([0xfe, 0xff, 0xff, 0xff, 0xfd, 0xff, 0x00, 0x20])

  adr_list = bytes([0x3, 0xff, 0x41, 0x03, 0x0])
  send_mac_command_linkadrreq(server, dev_eui, adr_list)
