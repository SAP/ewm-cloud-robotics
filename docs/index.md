# Description
Human-safe collaborative robots ("Cobots") are widely available from hundreds of low-cost vendors, leading to heterogenous fleets of cobots that need to easily integrate with corresponding management systems. **ewm-cloud-robotics** represents such an integration, leveraging the core of Google Cloud Robotics ([repo](https://github.com/googlecloudrobotics/core), [doc](https://googlecloudrobotics.github.io/core/)) to package and distribute [applications](cloud-robotics-apps.md) for autonomous fulfilment of warehouse orders & tasks commissioned by [SAP EWM (Extended Warehouse Management](https://www.sap.com/germany/products/extended-warehouse-management.html)) just like in the video below.
<div align="center">
  <a href="https://youtu.be/CFo4-BlGO74"><img src="https://img.youtube.com/vi/CFo4-BlGO74/0.jpg" alt="EWM Cloud Robotics"></a>
</div>

# Documentation
- [Architecture](architecture.md): Develop a deeper understanding about our architecture.
- [Apps](cloud-robotics-apps.md): Learn more about our apps.
- **Deployment**: Find out how to deploy EWM Cloud Robotics in different ways.
  - [Prepare your machine](prepare-your-machine.md): Prepare you local machine to build and deploy EWM Cloud Robotics
  - [Setup EWM](setup-EWM.md): Setup your EWM system. You don't have a running SAP EWM handy? Have a look the pre-packaged [SAP S/4HANA bundle provided by SAP CAL](https://blogs.sap.com/2018/12/12/sap-s4hana-fully-activated-appliance-create-your-sap-s4hana-1809-system-in-a-fraction-of-the-usual-setup-time/). We did the same.
  - [Deploy EWM simulator](deploy-EWM-simulator.md): You just want to test our solution without setting up the EWM processes? Please check our EWM simulator.
  - [Deploy Cloud Robotics K8S Apps](deployment.md): Finally, this is how you deploy our Kubernetes Apps.
- [Warehouse process flow](process-flow.md): Check how do robots process warehouse orders.  

# Interested?
Please have a look at the github repo of [EWM Cloud Robotics](https://github.com/SAP/ewm-cloud-robotics).