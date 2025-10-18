# Lab Setup For Contest Management

A robust, modular system for setting up a PC for onsite competitive programming contests, with intuitive configuration via editable files in the `config/` folder.

---

## 🚀 Usage Guide

See [Usage Guide](USAGE.md) for all commands and details.

---


## ✨ Features
- **Network Restrictions:** Block access to blacklisted sites (see `config/blacklist.txt`)
- **USB Controls:** Block USB storage devices
- **Easy CLI:** One command for setup, restrict, unrestrict, reset, and status
- **Persistent & Secure:** Survives reboot, systemd integration
- **Intuitive Config:** All user-editable lists (blacklist, package lists) are in the `config/` folder

---


## 🛠️ Requirements
- Ubuntu 18.04+ (or compatible Linux)
- Python 3.6+
- Root privileges for install/restriction

