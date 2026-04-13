# Scalable CAC & LTV Analytics Pipeline: Passive vs. Robo-Advisor

## 📊 Project Overview
Inspired by Warren Buffett’s 10-year bet, this project implements a scalable data pipeline to analyze the **"Hard Truth"** of investment fees and platform unit economics. 
It transforms raw transactional logs into a comparative analysis of **Self-Directed Passive Investing** vs. **Robo-Advisory** models.

The pipeline specifically addresses the **Unit Economics Problem**: 
Calculating how a high CAC and high churn create a structural "Payback Problem" for robo-advisors compared to low-cost passive alternatives.

---

## 📉 Core Metrics & Logic

| Metric | Business Logic | Data Source |
| :--- | :--- | :--- |
| **CAC** | $650+ (Robo) vs. $35 (Passive) | Sacra (2024) / Industry Benchmarks |
| **Annual Churn** | 25% (Financial/Credit Avg) | Deloitte / Aspect Consumer Index |
| **LTV:CAC Ratio** | Target: >3.0x for healthy unit economics | Modeled via Cumulative Fee Revenue |
| **Fee Drag** | Compounded impact of platform fees over $n$ years | Realized Portfolio Delta |

---
