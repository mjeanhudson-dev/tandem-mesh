---
id: "cmd-powershell-get-service-status"
title: "Get-Service-Status"
description: "Queries and outputs the current operational status of system services"
use_cases:
  - "Diagnosing stopped or degraded background daemons"
  - "Checking service availability before deployment"
syntax: "Get-Service -Name <ServiceName> | Select-Object Name, Status, StartType"
execution_environment: "powershell"
tags:
  - "commands/powershell"
  - "type/system"
  - "domain/monitoring"
aliases:
  - "check-service"
timestamps:
  created: "2026-11-01T06:00:00.000-04:00"
  updated: "2026-11-01T06:00:00.000-04:00"
parameters:
  - name: "-Name"
    type: "string"
    required: true
    description: "Name or pattern of target service"
safety_level: "read-only"
catalog: "aether"
type: "command-catalog"
version: "1.0.0"
---

# Get-Service-Status

## Description
Queries and outputs the current operational status of system services.

## Use Cases
- Diagnosing stopped or degraded background daemons
- Checking service availability before deployment

## Syntax
```powershell
Get-Service -Name <ServiceName> | Select-Object Name, Status, StartType
```
