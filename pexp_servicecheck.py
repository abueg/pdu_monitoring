#!/usr/bin/env python3.13

import pexpect
import re
import tomllib

VOLT_REGEX = r"voltage\s*: (?P<voltage>\d{1,3}\.\d)V"
CURR_REGEX = r"current\s*: (?P<current>\d{1,2}\.\d)A"
APC_REGEX = VOLT_REGEX + "\r\r\n" + CURR_REGEX
PROMPT = "apc>"
CHECKMK_OK_STATUS = 0
CHECKMK_WARN_STATUS = 1
CHECKMK_CRIT_STATUS = 2
CHECKMK_UNKN_STATUS = 3
CHECKMK_DYNAMIC_STATUS = "P"

def template_pdu():
    pdu_template = {}
    pdu_template["unit_voltage"] = None
    pdu_template["unit_current"] = None
    for i in range(1,4):
        pdu_template[f"phase_{i}_voltage"] = None
        pdu_template[f"phase_{i}_current"] = None
    for i in range(1,7):
        pdu_template[f"bank_{i}_voltage"] = None
        pdu_template[f"bank_{i}_current"] = None
    return pdu_template

def apc_cmd(px_obj, prompt, cmdline=str):
    """
    px_obj is the pxssh object
    prompt = prompt
    cmdline = apc cmd
    """
    px_obj.sendline(cmdline)   # run a command
    px_obj.expect(prompt)            # match the prompt
    cmd_out = px_obj.before        # save everything before the prompt
    cmd_out_str = cmd_out.decode('utf-8')
    return cmd_out_str

def piggyback_failed(service_name, fail_message):
    output = f'{CHECKMK_UNKN_STATUS} - "{service_name}" - {fail_message}'
    return output

def piggyback(service, service_val, service_name,
              service_unit, warn_low, crit_low, warn_high, crit_high):
    '''
    the expected string for the service is:
    metricname=value;warn_lower:warn_upper;crit_lower:crit_upper
    the above mapped to the variables piggyback() ingests is:
    "service_name" service_name=service_val;warn_low:warn:high;crit_low:crit_high service_name: service_val service_unit
    '''
    if service_val:
        piggyback_service = f'{CHECKMK_DYNAMIC_STATUS} "{service_name}" {service}={service_val};{warn_low}:{warn_high};{crit_low}:{crit_high} {service_name}: {service_val} {service_unit}'
    else:
        piggyback_failed(service_name, "failed to retrieve value")
    return piggyback_service

def checkmk_report(piggyback_results):
    print(f'<<<<{piggyback_host}>>>>\n<<<local>>>')
    for result in piggyback_results:
        print(result)
    print(f'<<<<>>>>\n<<<local:sep(0)>>>')

def piggyback_iterate(pdu_dictionary, pdu_config, default_volt_thres):
    ## input: pdu_dictionary to iterate over
    ## input: pdu_config to grab thresholds
    ## input: default_volt_thres for voltage defaults
    ## output: results_list with piggyback output text

    ### grab PDU-specific curr/volt thresholds from config
    default_volt = default_volt_thres
    if "current" in pdu_config["thresholds"]:
        current_thres = pdu_config["thresholds"]["current"]
    voltage_thres = pdu_config["thresholds"].get("voltage", default_volt)

    results_list = []

    for service,value in pdu_dictionary.items():
        service_scope = service.split("_")[0]
        service_metric = service.split("_")[-1]
        service_name = service.replace("_"," ").capitalize()
        if value and value != "pexp_failure":
            if service_metric == "voltage":
                service_unit = "V"
                service_thres = voltage_thres
                results_list.append(piggyback(
                    service=service_metric, service_val=value,
                    service_name=service_name, service_unit=service_unit,
                    warn_low=service_thres[f"{service_scope}_low_warn"],
                    crit_low=service_thres[f"{service_scope}_low_crit"],
                    warn_high=service_thres[f"{service_scope}_high_warn"],
                    crit_high=service_thres[f"{service_scope}_high_crit"]
                    ))
            if service_metric == "current":
                service_unit = "A"
                service_thres = current_thres
                results_list.append(piggyback(
                    service=service_metric, service_val=value,
                    service_name=service_name, service_unit=service_unit,
                    warn_low="", crit_low="",
                    warn_high=service_thres[f"{service_scope}_high_warn"],
                    crit_high=service_thres[f"{service_scope}_high_crit"]
                    ))
        if value == "pexp_failure":
            results_list.append(piggyback_failed(service_name, "failed to connect with pexpect"))
        if not value:
            results_list.append(piggyback_failed(service_name, "failed to parse output for service value"))

    return results_list

if __name__ == "__main__":
    ######################
    ### config stuff

    with open("config.toml", mode="rb") as fp:
        config = tomllib.load(fp)

    ## load global volt thresholds (can be overriden per-pdu later on)
    default_volt_thres = config["site_thresholds"]["voltage"]

    ######################
    ### iterate over PDUs

    for pdu_name,pdu_config in config["pdus"].items():
        if pdu_config["access"] == "ssh": 
            hostname = pdu_config["ip"]
            username = pdu_config["apc_login"]
            password = pdu_config["apc_secret"]
            piggyback_host = pdu_config["piggyback_host"]

            this_pdu = template_pdu()

            ### ssh session and populating PDU dict
            try:
                child = pexpect.spawn(f'ssh -l {username} {hostname}')
                child.expect("password:")
                child.sendline(password)
                child.expect(PROMPT)
            except:
                this_pdu = {key: "pexp_failure" for key in this_pdu}
            else:
                ### print unit 1 information: voltages and amperages
                unit_out = apc_cmd(child, PROMPT, "pwr unit 1")
                unit_capgroups = re.search(APC_REGEX, unit_out, re.MULTILINE)
                if unit_capgroups:
                    this_pdu["unit_voltage"] = unit_capgroups.group("voltage")
                    this_pdu["unit_current"] = unit_capgroups.group("current")

                ### print phase [123] information: voltages and amperages
                for i in range(1,4):
                    phase_out = apc_cmd(child, PROMPT, f"pwr phase {i}")
                    phase_capgroups = re.search(APC_REGEX, phase_out, re.MULTILINE)
                    if phase_capgroups:
                        this_pdu[f"phase_{i}_voltage"] = phase_capgroups.group("voltage")
                        this_pdu[f"phase_{i}_current"] = phase_capgroups.group("current")

                ### print bank [123456] information: voltages and amperages
                for i in range(1,7):
                    cb_out = apc_cmd(child, PROMPT, f"pwr cb {i}")
                    cb_capgroups = re.search(APC_REGEX, cb_out, re.MULTILINE)
                    if cb_capgroups:
                        this_pdu[f"bank_{i}_voltage"] = cb_capgroups.group("voltage")
                        this_pdu[f"bank_{i}_current"] = cb_capgroups.group("current")
                child.sendline("exit")
                child.expect("Connection Closed, Goodbye")

            ######################
            ### printing results

            ### iterate over PDU dict and save results to this_pdu_results
            ### also grabs current/volt thresholds from pdu_config
            ### plus the default volt thres from the config
            this_pdu_results = piggyback_iterate(this_pdu,
                                                 pdu_config,
                                                 default_volt_thres)

            ### print checkmk-formatted results
            checkmk_report(this_pdu_results)