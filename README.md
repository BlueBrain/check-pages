# check-pages

This repository contains code to check webpages and/or webportals in various ways. The following sections explain the code and the implementation within continuous integration.

## Code

### `pagechecker`

This code uses selenium (actually seleniumwire) to try to fully load random or all pages of a given set of URLs. For each URL the selenium webdriver is used to open the page and to perform all required http request calls. 

If any of the request has an status code >= 400, then this particular test is marked as *failed*. 

### `page_dom_check`

This code also uses selenium, but checks for the presence of certain expected DOM elements. 

The pages to test and the expected DOM elements are defined in a json file whcih looks like this:


    {
    	"exp_LayerAnatomy": {
    		"urls": "resources/SSCX_Portal/exp_LayerAnatomy.txt",
    		"ids": ["layerThickness", "neuronDensity", "layerAnatomySummary"],
    		"classes": []
    	},
    	"exp_neuronMorphology": {
    		"urls": "resources/SSCX_Portal/exp_neuronMorphology.txt",
    		"ids": ["metadata", "morphologyDownloadBtn", "morphometrics", "expMorphMemodelList", "expMorphologyTable"],
    		"classes": ["morpho-viewer"]
    	},
    }

For each section the following elements are defined:

  * `key`: Name of the section
  * `urls`: File that contains a list of URLs, each supposed to have the same set of DOM ids/classes.
  * `ids`: List of expected ids in the DOM in each of the URL.
  * `classes`: List of expected classes in the DOM in each of the URL.

In case a certain element is not found for any of the used URL's,  then this particular test is marked as *failed*. 

### `location_test`

This test uses the API of GTMetrix to load the given URL(s) on various locations around the world.

The URL's to test are defined in a json file:

    {
    	"domain": "https://bbp.epfl.ch/sscx-portal",
    	"urls":[
    		"/experimental-data/neuron-morphology/?instance=og060523b1-2_idD&layer=L6&mtype=L6_BTC",
        	"/experimental-data/neuron-electrophysiology/?etype=cADpyr&etype_instance=C061208B2-SR-C1",
        	"/digital-reconstructions/neurons/?brain_region=S1FL&layer=L23&etype=bNAC&mtype=L23_NGC&memodel=L23_NGC_bNAC_2",
        	"/"
    	]
    }

On the free plan 4 URLs can be tested from 4 free locations per day which are: 

  * Vancouver, CA
  * London, GB
  * San Antonio, US
  * Hong Kong, CN

As this is a performance test, the results are added to a [google spreadsheet](https://docs.google.com/spreadsheets/d/17BIK3-sR0gxRzrYgtsg4LnmKpg9Sff_50eC6B0PBaLc/edit)
.



### slack_reporter

This is just a helper tool used for the first two tools to automatically report the results on slack (**ok** or **not ok**).


## CI

In the CI in gitlab of this repository there are currently 4 jobs that are scheduled to run automatically.

### `check_pages_sscx`

  * testing: SSCX Portal
  * schedule: weekly
  * code: pagechecker

### `check_dom_sscx`

  * testing: SSCX Portal
  * schedule: weekly
  * code: page_dom_check

### `check_links`

  * testing: BBP Portal
  * schedule: weekly
  * code: pylinkvalidate (third party tool)

### `location_testing_sscx`


  * testing: SSCX Portal
  * schedule: daily
  * code: location_test