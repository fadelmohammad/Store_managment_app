\# PROJECT STATE

\#\# System Overview

Python-based store management / POS system.

\#\# Modules

\* Inventory: basic structure exists  
\* Sales: partial implementation  
\* Accounting: not fully integrated  
\* UI: basic interface

\#\# Current Status

System is in early development stage.  
Core flows are not fully connected.

\#\# Known Issues

\* Payment does not update ledger  
\* Inventory not reduced after sale  
\* Data flow between modules unclear

\#\# Recent Changes

\* Initial project setup  
\* Basic modules created

\#\# Next Tasks

1\. Define correct data flow (sale → payment → ledger → inventory)  
2\. Fix accounting integration  
3\. Separate modules properly

\#\# Data Flow (Expected)

Sale → Invoice → Payment → Ledger update → Inventory update

\#\# Notes

Architecture needs restructuring to separate logic from UI.

