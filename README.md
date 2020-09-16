## EOEPCA - Burned area

### About this application

This is a simple application used as an artifact for testing EOEPCA release 0.2

It validates the fan-in with stage-in paradigm where Sentinel-2 acquisitions staged as STAC are processed to the burned area using NDVI and NDWI.  

### Build the docker

The repo contains a Dockerfile and a Jenkinsfile.  

The build is done by Terradue's Jenkins instance with the configured job https://build.terradue.com/job/containers/job/eoepca-burned-area/

### Create the application package

Run the command below to print the CWL: 

```bash
docker run --rm -it terradue/eoepca-burned-area:0.1 burned-area --docker 'terradue/eoepca-burned-area:0.1'
```

Save the CWL output to a file called `eoepca-burned-area.cwl`

Package it as an application package wrapped in an Atom file with:

```bash
cwl2atom eoepca-burned-area > eoepca-burned-area.atom 
```

Post the Atom on the EOEPCA resource manager

### Application execution

Use the parameters:

* **pre_event**: https://catalog.terradue.com/sentinel2/search?uid=S2B_MSIL2A_20200130T004659_N0213_R102_T53HPA_20200130T022348
* **post_event**: https://catalog.terradue.com/sentinel2/search?uid=S2A_MSIL2A_20191216T004701_N0213_R102_T53HPA_20191216T024808
* **ndvi_threshold**: 0.19
* **ndwi_threshold**: 0.18