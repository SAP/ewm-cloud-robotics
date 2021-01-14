# Deployment

## Cloud Robotics cluster
If you don't have a Cloud Robotics cluster yet, follow the instructions given [here](https://googlecloudrobotics.github.io/core/how-to/deploy-from-sources) to set up your Google Cloud Platform (GCP) project containing the Cloud Robotics Core.

## Container registry
You can use the default images for all apps we publish at [docker hub](https://hub.docker.com/u/ewmcloudrobotics) and skip this step. If you have modified the images and would like to use the GCR of your project you can either use the predefined skaffold profile to build, test & push all images (1), or build images required for single cloud robotics applications (2). Within both options the container registry is dynamically generated based upon your gcloud configuration (`gcloud config get-value project` - configurable via `gcloud config set project <GCP_PROJECT>`) and host `eu.gcr.io`. Consequently, images are pushed to `eu.gcr.io/<GCP_PROJECT>/<IMAGE_NAME>`. You can also use a specific container registry (3), it is assumed that access has been established beforehand. 
```bash
# (1)
skaffold run --profile gcp

# (2)
./deploy.sh build ewm-order-manager

# (3)
./deploy.sh --registry=eu.gcr.io/my-gcp-project build ewm-order-manager
```

## Configuration
In order to customize the settings of any Cloud Robotics application, adjust the YAML of the [AppRollout](https://github.com/SAP/ewm-cloud-robotics/tree/master/applayer-yaml). It allows overwriting all variables of the underlying [helm chart](https://github.com/SAP/ewm-cloud-robotics/tree/master/helm/charts). By default the `deploy.sh` script uses the `approllout.yaml`/`app.yaml` files at `~/.config/ewm-cloud-robotics-deployments/<GCP_PROJECT>/<APP>/`, thus one gets the best user experience by doing the following:
```bash
# (1) create the dir
mkdir -p ~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)

# (2) copy the templates to the created dir
cp -R applayer-yaml/ ~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)

# (3) verify that app folders are in the correct place (expected print: 6 app directories)
ls ~/.config/ewm-cloud-robotics-deployments/$(gcloud config get-value project)
```
If you work on multiple projects, switch your gcloud project configuration and repeat the steps above. This way you do not interfere with any of your previous configurations. Alternatively copy the AppRollout template files to adjust the values and continue using the copy within the installation process by specifying the path via the corresponding flag (`./deploy.sh -f <path> rollout <APP>`).

## Installation
Installing the apps to your Google Cloud Robotics cluster is a two-step process (ref. [Cloud Robotics Application Management](https://googlecloudrobotics.github.io/core/concepts/app-management.html)): 
1. Make your application available in the Google Cloud Robotics cluster by creating an App that describes which Helm charts should run in the respective cloud/robot targets.
2. Instantiate your application by creating an AppRollout referencing the previously created App. The AppRollout contains your specific configurations for your ewm-cloud-robotics deployment.

If you have complected the [configuration steps](#configuration), you can leverage the `deploy.sh` script as follows:
```bash
# Example: ewm-order-manager

# (1) Register 'dev' version of the ewm-order-manager App
./deploy.sh push ewm-order-manager

# (2) Create a corresponding AppRollout
./deploy.sh rollout ewm-order-manager
```
Otherwise you need to specify `approllout.yaml`/`app.yaml` files for `push` and `rollout`. You can get examples and further information about this by running `./deploy.sh help`.