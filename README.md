# CDP DoS Attack – How‑to Guide

## Introduction
In this repository we demonstrate a Cisco Discovery Protocol (CDP) **Denial of Service (DoS)** attack within a controlled laboratory environment. The purpose is to show how an attacker can exploit CDP by sending a flood of CDP packets to a switch, causing its CPU to spike and eventually degrade network performance. This guide walks you through setting up the lab, running the attack script, observing its impact, and applying mitigation techniques.

**Responsible Use:**
This project is for educational and research purposes only. Execute the scripts only in a lab environment where you have permission. Do not use these techniques on production networks.

## Prerequisites

- A GNS3 lab or similar virtualization environment.
- Cisco IOSvL2 switch and router images with CDP enabled.
- A Kali Linux VM (attacker) with Python 3 installed.
- A victim host (e.g., VPCS or Linux).
- Base IP network `20.25.8.0/24` configured on all devices.
- Root or sudo privileges on the attacker machine.
- Cloned repository [`iClexi/CDP-Attack`](https://github.com/iClexi/CDP-Attack).

Below is the topology used in this lab:

![Lab topology](images/topology.png)

| Device | Interface | IP address | Role |
|-------|-----------|------------|------|
| **R‑1 (Router)** | F0/0 | `20.25.8.45/24` | Gateway |
| **SW‑1 (Switch)** | Gi0/1, Gi0/2 | — | Layer‑2 switch |
| **Kali (Attacker)** | eth0 | `20.25.8.46/24` | Attacker |
| **PC1 (Victim)** | — | `20.25.8.47/24` | Victim |

Ensure basic connectivity between the attacker, victim and router before running the attack (e.g. `ping 20.25.8.45` from PC1).

## Installation and setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/iClexi/CDP-Attack.git
   cd CDP-Attack
   ```

2. **Install dependencies** on Kali:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   pip3 install scapy
   ```

3. **Configure network devices:**
   - Enable CDP on the switch and router (default behaviour).
   - Assign the IP addresses shown in the topology.
   - Verify connectivity from PC1 to the router with `ping 20.25.8.45`.

## Running the attack

The attack script is `cdp-attack.py`. It sends a burst of CDP packets with customizable payload size, pool size and worker threads. Adjust parameters according to your lab resources.

**Example command:**

```bash
sudo python3 cdp-attack.py -i eth0 --yes \
  --workers 4 \
  --pool 3000 \
  --payload-size 1500 \
  --extra 1400 \
  --duration 60
```

- `-i eth0` – interface connected to the switch.
- `--workers` – number of parallel processes (defaults to CPU count).
- `--pool` – number of packets per worker to pre‑generate.
- `--payload-size` – size of each CDP packet (max 1500 bytes).
- `--extra` – extra bytes appended in the software description TLV.
- `--duration` – attack duration in seconds (`0` is unlimited).
- `--yes` – skip interactive confirmation.

During the attack the script prints statistics about packets sent and the average packets per second.

![Running the attack on Kali](images/script_execution.png)

## Observing the impact

On the switch, monitor the CPU utilisation and CDP neighbours to see the effect of the attack.

### CPU usage before the attack

```plaintext
SW1# show processes cpu sorted
```

![CPU before attack](images/cpu_before.png)

### CPU usage during the attack

```plaintext
SW1# show processes cpu sorted
```

![CPU during attack](images/cpu_after.png)

Notice how the CPU utilisation increases when the CDP flood is sent.

### CDP neighbours after flooding

Run:

```plaintext
SW1# show cdp neighbors
```

You should see hundreds or thousands of fake CDP entries learned on the attacker’s port:

![CDP neighbours flood](images/cdp_neighbors.png)

The script also prints the number of CDP entries displayed, for example:

![Total CDP entries](images/cdp_entries.png)

These entries confirm the flood’s effect on the switch.

## Mitigation techniques

Two primary mitigations can stop CDP‑based DoS attacks:

### 1. Disable CDP globally

If CDP is not required, disable it on the entire device:

```plaintext
SW1(config)# no cdp run
SW1# show cdp neighbors
% CDP is not enabled
```

![CDP disabled globally](images/cdp_disabled_global.png)

This prevents any CDP packets from being processed.

### 2. Disable CDP on untrusted interfaces

If CDP is needed on management ports but not on user‑facing ports, disable it per interface:

```plaintext
SW1(config)# interface gigabitEthernet0/1
SW1(config-if)# no cdp enable
SW1# show cdp neighbors
% CDP is not enabled
```

![CDP disabled on interface](images/cdp_disabled_interface.png)

This stops CDP processing only on the specified interface, leaving CDP running elsewhere.

After applying the mitigation, repeat the attack and observe that the CPU remains low and the CDP neighbours do not increase.

## Conclusion

This guide demonstrates how an adversary can exploit Cisco Discovery Protocol by flooding a switch with crafted CDP packets to exhaust CPU resources. By following the steps above, you can reproduce the attack in a lab environment and observe its impact. Always implement the recommended mitigations — disabling CDP globally or on user‑facing ports — to protect your network from such DoS attacks.

For more details about the script parameters, technical notes and troubleshooting, refer to the `mitigacion-cdp-attack.md` file in this repository and the original video tutorial.
