# Project for monitoring data center APC PDUs

## Overview

This project houses scripts used for monitoring APC PDUs. 

- The scripts' outputs are formatted as [checkmk local checks](https://docs.checkmk.com/latest/en/localchecks.html).
    - Checks are meant to be run on a ['piggyback host'](https://docs.checkmk.com/latest/en/piggyback.html) which can grab PDU information (instead of running the checks on the PDUs themselves).
    - Upper WARN/CRIT thresholds are customizable.
- The scripts parse a `config.toml` file expected in the same directory as the script being invoked.
    - See `config.example.toml` for examples. 

### `pexp_servicecheck.py`
- Uses the `pexpect` package to connect to PDUs via ssh and query them for information (it reads login credentials for the PDU from the `config.toml`).
- Pulls **phase, bank, and unit** voltages/currents.

### `snmp_servicecheck.py`
- Uses `subprocess.run()` to do SNMP queries for PDUs.
- Pulls **phase-to-phase voltage** information. 

## Output examples

### SSH-based CLI output

APC PDU command-line interface output looks like the following:

<details>

<summary>click to expand CLI example</summary>

```
## phase [123]
apc>pwr phase 1
SUCCESS
PHASE 1 power Feature
voltage       : 199.4V
current	      : 0.0A
activepower   : 0.0W
apparentpower : 0.000VA
powerfactor   : 0.00
energy        : 0.000kWh

## bank [123456]
apc>pwr cb 1

SUCCESS
CB 1 power Feature
voltage       : 200.4V
current	      : 0.0A
activepower   : 0.0W
apparentpower : 0.000VA
powerfactor   : 1.00
energy        : 0.000kWh

## unit 1 (we don't daisy chain)
apc>pwr unit 1

SUCCESS
UNIT power Feature
voltage       : 200.5V
current	      : 0.0A
activepower   : 0.0W
apparentpower : 0.000VA
powerfactor   : 1.00
energy        : 0.000kWh
```

</details>

The `pexp_servicecheck.py`'s checkmk output looks like this (example is with two PDUs):

```
<<<<pdu1>>>>
<<<local>>>
P "Unit voltage" voltage=197.6;190:215;180:225 Unit voltage: 197.6 V
P "Unit current" current=21.3;:98.4;:115.2 Unit current: 21.3 A
P "Phase 1 voltage" voltage=199.9;190:215;180:225 Phase 1 voltage: 199.9 V
P "Phase 1 current" current=5.7;:32.8;:38.4 Phase 1 current: 5.7 A
P "Phase 2 voltage" voltage=197.4;190:215;180:225 Phase 2 voltage: 197.4 V
P "Phase 2 current" current=7.5;:32.8;:38.4 Phase 2 current: 7.5 A
P "Phase 3 voltage" voltage=197.6;190:215;180:225 Phase 3 voltage: 197.6 V
P "Phase 3 current" current=8.1;:32.8;:38.4 Phase 3 current: 8.1 A
P "Bank 1 voltage" voltage=199.5;190:215;180:225 Bank 1 voltage: 199.5 V
P "Bank 1 current" current=0.0;:14;:16 Bank 1 current: 0.0 A
P "Bank 2 voltage" voltage=197.3;190:215;180:225 Bank 2 voltage: 197.3 V
P "Bank 2 current" current=2.7;:14;:16 Bank 2 current: 2.7 A
P "Bank 3 voltage" voltage=197.8;190:215;180:225 Bank 3 voltage: 197.8 V
P "Bank 3 current" current=0.8;:14;:16 Bank 3 current: 0.8 A
P "Bank 4 voltage" voltage=200.3;190:215;180:225 Bank 4 voltage: 200.3 V
P "Bank 4 current" current=3.1;:14;:16 Bank 4 current: 3.1 A
P "Bank 5 voltage" voltage=197.6;190:215;180:225 Bank 5 voltage: 197.6 V
P "Bank 5 current" current=3.1;:14;:16 Bank 5 current: 3.1 A
P "Bank 6 voltage" voltage=197.4;190:215;180:225 Bank 6 voltage: 197.4 V
P "Bank 6 current" current=3.2;:14;:16 Bank 6 current: 3.2 A
<<<<>>>>
<<<local:sep(0)>>>
<<<<pdu2>>>>
<<<local>>>
P "Unit voltage" voltage=197.7;190:215;180:225 Unit voltage: 197.7 V
P "Unit current" current=8.0;:98.4;:115.2 Unit current: 8.0 A
P "Phase 1 voltage" voltage=199.6;190:215;180:225 Phase 1 voltage: 199.6 V
P "Phase 1 current" current=3.4;:32.8;:38.4 Phase 1 current: 3.4 A
P "Phase 2 voltage" voltage=198.0;190:215;180:225 Phase 2 voltage: 198.0 V
P "Phase 2 current" current=0.9;:32.8;:38.4 Phase 2 current: 0.9 A
P "Phase 3 voltage" voltage=197.7;190:215;180:225 Phase 3 voltage: 197.7 V
P "Phase 3 current" current=3.6;:32.8;:38.4 Phase 3 current: 3.6 A
P "Bank 1 voltage" voltage=199.8;190:215;180:225 Bank 1 voltage: 199.8 V
P "Bank 1 current" current=0.4;:14;:16 Bank 1 current: 0.4 A
P "Bank 2 voltage" voltage=198.0;190:215;180:225 Bank 2 voltage: 198.0 V
P "Bank 2 current" current=0.7;:14;:16 Bank 2 current: 0.7 A
P "Bank 3 voltage" voltage=197.8;190:215;180:225 Bank 3 voltage: 197.8 V
P "Bank 3 current" current=3.4;:14;:16 Bank 3 current: 3.4 A
P "Bank 4 voltage" voltage=199.4;190:215;180:225 Bank 4 voltage: 199.4 V
P "Bank 4 current" current=0.0;:14;:16 Bank 4 current: 0.0 A
P "Bank 5 voltage" voltage=198.1;190:215;180:225 Bank 5 voltage: 198.1 V
P "Bank 5 current" current=0.1;:14;:16 Bank 5 current: 0.1 A
P "Bank 6 voltage" voltage=197.6;190:215;180:225 Bank 6 voltage: 197.6 V
P "Bank 6 current" current=0.0;:14;:16 Bank 6 current: 0.0 A
<<<<>>>>
<<<local:sep(0)>>>
```

### SNMP-based output

For the following OID...

```
snmpwalk -v 2c -c public ${PDU_IP} .1.3.6.1.4.1.318.1.1.26.13.1.1

SNMPv2-SMI::enterprises.318.1.1.26.13.1.1.1.1 = INTEGER: 1
SNMPv2-SMI::enterprises.318.1.1.26.13.1.1.2.1 = INTEGER: 1
SNMPv2-SMI::enterprises.318.1.1.26.13.1.1.3.1 = INTEGER: 198
SNMPv2-SMI::enterprises.318.1.1.26.13.1.1.4.1 = INTEGER: 198
SNMPv2-SMI::enterprises.318.1.1.26.13.1.1.5.1 = INTEGER: 199
```

... the `*.[345].1` values are the phase-to-phase voltages we want. 

The `snmp_servicecheck.py`'s checkmk output looks like this:

```
<<<<pdu3>>>>
<<<local>>>
P "Phase 1-to-2 voltage" voltage=198;190:215;180:225 Phase 1-to-2 voltage: 198 V
P "Phase 2-to-3 voltage" voltage=198;190:215;180:225 Phase 2-to-3 voltage: 198 V
P "Phase 3-to-1 voltage" voltage=199;190:215;180:225 Phase 3-to-1 voltage: 199 V
<<<<>>>>
<<<local:sep(0)>>>
<<<<pdu4>>>>
<<<local>>>
P "Phase 1-to-2 voltage" voltage=198;190:215;180:225 Phase 1-to-2 voltage: 198 V
P "Phase 2-to-3 voltage" voltage=198;190:215;180:225 Phase 2-to-3 voltage: 198 V
P "Phase 3-to-1 voltage" voltage=199;190:215;180:225 Phase 3-to-1 voltage: 199 V
<<<<>>>>
<<<local:sep(0)>>>
```
