#!/usr/bin/env python3.13

import subprocess
import tomllib
from pexp_servicecheck import piggyback
from pexp_servicecheck import piggyback_failed

ph2ph_volt_oid_base = ".1.3.6.1.4.1.318.1.1.26.13.1.1"
voltage_oids = {
    "1-to-2":f"{ph2ph_volt_oid_base}.3.1",
    "2-to-3":f"{ph2ph_volt_oid_base}.4.1",
    "3-to-1":f"{ph2ph_volt_oid_base}.5.1"
}
snmp_cmd_flags = ["-v", "2c", "-c", "public", "-Oqv"]

with open("config.toml", mode="rb") as fp:
    config = tomllib.load(fp)

## load global volt thresholds (can be overriden per-pdu later on)
default_volt_thres = config["site_thresholds"]["voltage"]

for pdu_name,pdu_info in config["pdus"].items():
    if pdu_info["access"] == "snmp":
        piggyback_host = pdu_info["piggyback_host"]
        print(f'<<<<{piggyback_host}>>>>\n<<<local>>>')
        
        if "current" in pdu_info["thresholds"]:
            curr_thres = pdu_info["thresholds"]["current"]
        volt_thres = pdu_info["thresholds"].get("voltage", default_volt_thres)

        for volt_type,oid in voltage_oids.items():
            snmp_cmd = []
            snmp_cmd.append("snmpget")
            for flag in snmp_cmd_flags:
                snmp_cmd.append(flag)
            snmp_cmd.append(pdu_info["ip"])
            snmp_cmd.append(oid)
            snmp_out = subprocess.run(snmp_cmd, capture_output=True, text=True).stdout.rstrip()
            if snmp_out:
                print(piggyback(
                    service=f"voltage", service_val=snmp_out,
                    service_name=f"Phase {volt_type} voltage", service_unit="V",
                    warn_low=volt_thres["ph2ph_low_warn"], crit_low=volt_thres["ph2ph_low_crit"],
                    warn_high=volt_thres["ph2ph_high_warn"], crit_high=volt_thres["ph2ph_high_crit"]
                ))
            else:
                piggyback_failed(f"Phase {volt_type} voltage")

        print(f'<<<<>>>>\n<<<local:sep(0)>>>')
