## EOEPCA - Burned area

### About this application

This is a simple application used as an artifact for testing EOEPCA release > 0.3

It validates the fan-in with stage-in paradigm where Sentinel-2 acquisitions staged as STAC are processed to the burned area using NDVI and NDWI.  

### Build the docker

The repo contains a Dockerfile and a Jenkinsfile.  

The build is done by Terradue's Jenkins instance with the configured job https://build.terradue.com/job/containers/job/eoepca-burned-area/

### Create the application package

Package it as an application package wrapped in an Atom file with:

```bash
cwl2atom burned-area.cwl > eoepca-burned-area.atom 
```

Post the Atom on the EOEPCA resource manager catalog

### Application execution

#### Stage-in

Create a YAML file with the pre-event acquisition:

instac-pre.yml
```yaml
store_username: ''
store_apikey: ''
input_reference:
- https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_36RTT_20191205_0_L2A 
```

instac-post.yml
```yaml
store_username: ''
store_apikey: ''
input_reference:
- https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_36RTT_20191215_0_L2A 
```

Stage the STAC items as a local STAC catalog with:

```console
cwltool instac.cwl instac-pre.yml
```


```console
cwltool instac.cwl instac-post.yml
```

Check the output and copy the results paths.

#### Running the application

Create a YAML file with:

burned-area.yml
```yaml
pre_event: { class: Directory, path: file:///workspace/eoepca/app-burned-area/796_31mk}
post_event: { class: Directory, path: file:///workspace/eoepca/app-burned-area/umn3122s}
ndvi_threshold: '0.19'
ndwi_threshold: '0.18'
```

Run the application with:

```console
cwltool burned-area.cwl#burned-area burned-area.yml
```