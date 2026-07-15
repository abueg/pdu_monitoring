# Project for monitoring data center APC PDUs

This project houses scripts used for monitoring APC PDUs. 

- The scripts' outputs are formatted as [checkmk local checks](https://docs.checkmk.com/latest/en/localchecks.html).
    - Checks are meant to be run on a ['piggyback host'](https://docs.checkmk.com/latest/en/piggyback.html) which can grab PDU information (instead of running the checks on the PDUs themselves).
- The scripts parse a `config.toml` file expected in the same directory as the script being invoked.
    - See `config.example.toml` for examples. 

The `pexp_servicecheck.py` uses the `pexpect` package to connect to PDUs via ssh and query them for information (it reads login credentials for the PDU from the `config.toml`).

The `snmp_servicecheck.py` uses `subprocess.run()` to do SNMP queries for PDUs. 

