# Firegex Overview

---

## 📕 Firegex Docs

### 📡 Netfilter Regex Documentation

Netfilter Regex is a powerful feature that enables filtering of network packets using regular expressions. It's especially useful for inspecting packet content and matching specific strings or patterns.

### ⚙️ How to Use

1. Create a service
2. Attach regular expressions to it
3. Apply it to a network interface
4. Packets are dynamically filtered based on your regex patterns

### 🚀 How It Works

The packet filtering process is implemented in C++ with these key steps:

1. **Packet Interception** 🔍 - The nfqueue kernel module (netfilter) intercepts network packets. Rules are attached via nftables with JSON APIs through the Python manager.

2. **Packet Reading** 🧵 - A dedicated thread reads packets from nfqueue.

3. **Packet Parsing** 📄 - Libtins (C++ library) extracts packet payloads.

4. **Multi-threaded Analysis** ⚡️ - Multiple threads analyze packets concurrently. Unlike nfqueue's IP-based load balancing, Firegex balances using IP addresses combined with port hashing for better distribution, especially in NAT environments.

5. **TCP Handling** 📈 - Libtins uses a TCP follower to order out-of-order packets.

6. **Regex Matching** 🎯 - Vectorscan (Hyperscan fork supporting arm64) processes the payload. UDP packets are matched per-packet, saving only match context rather than full payload.
