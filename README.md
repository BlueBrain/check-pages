# 'check-pages' Project

Welcome to the check-pages repository!
This project is an open-source initiative aimed at testing UI features and functionality across
several webpages and webportals of the Blue Brain Project. It is designed to help ensure that the
web portals perform as expected and meet quality standards by running a suite of automated tests.

## Purpose

The goal of this project is to automate the testing of web portals, focusing on verifying
the correct behavior of various UI elements and overall user workflows; verifying URLs and
HTTP request calls.

## Features

* Automated tests for common UI interactions such as form submissions, button clicks,
* navigation flows, and presence of elements in the DOM.
* Cross-browser testing support to ensure compatibility with Chrome/ Firefox and in --headless mode
* Built-in reporting for tracking test results and identifying issues.

## Technology Stack

The tests are written using Selenium (also seleniumwire, seleniumbase), Python (pytest)
and integrated with CI Gitlab.

## Getting Started To get started with this project, follow the steps below:

1. **Clone the repository**:

```
git clone https:
```

2. **Install dependencies**:

Refer to the installation guide or the `requirements.txt` file to install any dependencies required
to run this project.

3. **Run the project**:

Follow the instructions provided in the [Usage](#usage) section.

## Usage

Once the dependencies are installed, you can run the project with the commands specified in
the `.gitlab-ci.yml` file.

## Code

### `pagechecker`

This code uses selenium (actually seleniumwire) to try to fully load random or all pages of a given
set of URLs. For each URL the selenium webdriver is used to open the page and to perform all
required http request calls.

If any of the request has a status code >= 400, then this particular test is marked as *failed*.

### `page_dom_check`

This implementation uses Selenium to verify the presence of specific expected DOM elements.

The pages to test and the expected DOM elements are defined in a json file which looks like this:

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

In case a certain element is not found for any of the used URL's, then this particular test is
marked as *failed*.

### `location_test`

Initially, the GTMetrix API was used to load the given URL(s) from various locations around the world.

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

Initially, on the free plan 4 URLs were tested from 4 free locations per day:

* Vancouver, CA
* London, GB
* San Antonio, US
* Hong Kong, CN

As this is a performance test, the results are added to
a [google spreadsheet](https://docs.google.com/spreadsheets/d/17BIK3-sR0gxRzrYgtsg4LnmKpg9Sff_50eC6B0PBaLc/edit).

The location tests were performed for the following portals:

* SSCX: 4 URL's from 4 locations (every odd day)
* HIPPO: 3 URL's from 4 locations (every even day)
* NGV: 1 URL from 4 locations (every even day)

With a free account on gtmetrix a user has 10 credits per day. Each of the above tests cost 0.6
credits (see [API documentation](https://gtmetrix.com/api/docs/2.0/)), so when testing 4 URL's from
4 locations these are 16 tests, costing 9.6 credits.

### `pytest`

Several `pytest` tests are defined to check some services/apps.

#### mooc_tests.py

This test setup is used to run Selenium tests to check several pages and services as defined
in `resources/Mooc/mooc_tests.json` in addition to extensive tests for the SimUI and PSPAPP. This
test logs in to edX and opens a special page where all the services are linked. For the tests listed
in `mooc_tests.json` the code only verifies the existence of a certain element.

For the tests of SimUI and PSPAPP, two tests (`start_simui` and `start_pspapp`) will start a simple
job on the GUI and stored the job-ID or result-URL in the file `SIMUI.INFO` and `PSPAPP.INFO`.

When the CI job is run again, the two tests `check_simui` and `check_pspapp` pick up these job-ID
and result-URL and check if the job as been completed successfully.

#### ebrains_tests.py
[NOTE] This test is no longer running as EBRAINS portal is no longer supported by the BBP.

This test setup us used to run selenium tests to check two SimUI ebrains services. Like the test
before this test stats two SimUI runs (on circuit `CA1` and circuit `MICROCIRCUIT`) and stores the
ID's in the files `SIMUI_CA1.INFO` and `SIMUI_MICRO.INFO`. In the next run of the job the results
are verified.

#### pick_test.py

This test setup checks the `pick-real-neuron` app by opening the page and clicking on a correct and
on an incorrect image. The overlay text is verified as well as the counter.

### page_dom_check.py

This test checks for certain DOM elements visible in the html page. See the description above.

### slack_reporter

This is just a helper tool used for the first two tools to automatically report the results on
slack (**ok** or **not ok**).

## CI

In the CI in gitlab of this repository there are currently 10 jobs that are scheduled to run
automatically.

### `check_ngvviewer`

* testing: NGV Viewer Status (https://bbp.epfl.ch/ngv-viewer/status)
* schedule: daily
* code: none (curl)

### `check_pages_sscx`

* testing: SSCX Portal
* schedule: weekly
* code: pagechecker

### `check_pages_hippo`

* testing: Hippocampus Portal
* schedule: weekly
* code: pagechecker

### `check_pages_nmc`

* testing: NMC Portal (only a subset)
* schedule: daily
* code: pagechecker

### `check_dom_sscx`

* testing: SSCX Portal (DOM elements)
* schedule: daily_even (every even day)
* code: page_dom_check

### `check_dom_hippo`

* testing: Hippocampus Portal (DOM elements)
* schedule: daily_even (every even day)
* code: page_dom_check

### `check_dom_ngv`

* testing: NGV Portal (DOM elements)
* schedule: daily_even (every even day)
* code: page_dom_check

### `check_links`

* testing: BBP Portal
* schedule: weekly
* code: pylinkvalidate (third party tool)

### `location_testing_sscx`

* testing: SSCX Portal
* schedule: daily_odd (odd days)
* code: location_test

### `location_testing_hippo`

* testing: SSCX Portal
* schedule: daily_even (even days)
* code: location_test

### `check_mooc`

* testing: MOOC Services (SimUI, PSPAPP, grader etc.)
* schedule: daily at 5:05
* code: pytest / mooc_tests.py
* remark: each CI-job starts a job for simui/pspapp, which gets verified on the next CI-job

### `check_ebrains`

(No longer running)

* testing: ebrains Services (SimUI)
* schedule: daily at 5:35
* code: py.test / ebrains_tests.py
* remark: each CI-job starts a job for both simui circuits, which gets verified on the next CI-job

### `check_pickneuron`

* testing: pick-the-neuron app
* schedule: daily at 6:05
* code: pytest / pick_test.py

## .gitlab-ci.yml

In this section the details of the used `.gitlab-ci.yml` file is explained.

```
.setup-env: &setup-env
    - apt-get update
    - apt-get install -y unzip curl software-properties-common  vim git python3-pip python3 xvfb
    - curl https://dl-ssl.google.com/linux/linux_signing_key.pub -o /tmp/google.pub
    - cat /tmp/google.pub | apt-key add -
    - echo 'deb http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google.list
    - mkdir -p /usr/share/desktop-directories
    - wget --no-verbose -O /tmp/chrome.deb http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_107.0.5304.87-1_amd64.deb && apt install -y /tmp/chrome.deb && rm /tmp/chrome.deb
    - dpkg-divert --add --rename --divert /opt/google/chrome/google-chrome.real /opt/google/chrome/google-chrome
    - echo -e "#!/bin/bash\nexec /opt/google/chrome/google-chrome.real --no-sandbox --disable-setuid-sandbox \"\$@\"" > /opt/google/chrome/google-chrome
    - chmod 755 /opt/google/chrome/google-chrome
    - google-chrome --version
    - wget --no-verbose https://chromedriver.storage.googleapis.com/107.0.5304.18/chromedriver_linux64.zip && unzip chromedriver_linux64.zip
    - export PATH=`pwd`:${PATH}
    - pip install -r requirements.txt
    - pip install -i https://bbpteam.epfl.ch/repository/devpi/simple .
```

This part creates the environment in which the selenium tests are being executed.
After installing the required linux packages the Chrome browser and the matching chromedriver is
installed. The latest version for chrome can be found
on [Chrome Releases](https://chromereleases.googleblog.com/search/label/Stable%20updates) and for
chromedriver [HERE](https://chromedriver.chromium.org/).

```
check_dom_sscx:
  variables:
    KUBERNETES_MEMORY_LIMIT: 10Gi
    KUBERNETES_MEMORY_REQUEST: 10Gi  
    KUBERNETES_CPU_REQUEST: 4
    KUBERNETES_CPU_LIMIT: 4
  stage: page_checks
  timeout: 3 hours
  rules:
    - if: $PIPELINE_SELECT == "daily_even"
    - if: $PIPELINE_SELECT == $CI_JOB_NAME
  image: python:3.8-buster
  script:
    - *setup-env
    - mkdir -p output
    - exit_code=0
    - Xvfb :99 &
    - export DISPLAY=:99
    - pytest -s check_pages/page_dom_check.py  --number 20 --params resources/SSCX_Portal/sscx_dom_check.json --domain https://sscx-portal.kcp.bbp.epfl.ch/sscx-portal --headless || exit_code=1
    - slack_reporter --ok_url $SLACK_LINK_OK --err_url $SLACK_LINK_NOK --name "SSCX Dom Check" --filename page_dom_check.log --status $exit_code
  artifacts:
    paths:
      - output
```

This example shows a job that is supposed to run every second day, which also can be triggered
manually by setting the variable `PIPELINE_SELECT` to `check_dom_sscx` (which is the name of the
job). This job also sets some increased memory and CPU limits.
For the environment it uses the `python:3.8-buster` image and creates the environment as explained
above.
The parts with the `Xvfb` and `DISPLAY` are required when the tests are not run headless, i.e. with
a GUI. In that case screenshots can also be made.
Finally, the `artifacts` part defines a folder that is retained which can be downloaded after the
test has run in order to see additional outputs or to debug in case of a failure.

```
check_mooc:
  stage: page_checks
  rules:
    - if: $PIPELINE_SELECT == "mooc"
    - if: $PIPELINE_SELECT == $CI_JOB_NAME
  image: bbpgitlab.epfl.ch:5050/nse/repo-checker-group/check-pages
  script:
    - pip install -r requirements.txt
    - pip install -i https://bbpteam.epfl.ch/repository/devpi/simple .
    - export http_proxy=http://bbpproxy.epfl.ch:80/
    - export https_proxy=http://bbpproxy.epfl.ch:80/
    - export no_proxy="localhost,127.0.0.1,localaddress,.localdomain.com"
    - export NO_PROXY="localhost,127.0.0.1,localaddress,.localdomain.com"
    - mkdir debug
    - exit_code=0
    - pytest -s check_pages/mooc_tests.py --tests resources/Mooc/mooc_tests.json --headless --wire || exit_code=1
    - cat service_results.txt
    - mv latest_logs debug
    - slack_reporter --ok_url $SLACK_LINK_OK --err_url $SLACK_LINK_NOK --name "MOOC Check" --filename service_results.txt --status $exit_code
  artifacts:
    paths:
      - debug
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - SIMUI_CA1.INFO
      - SIMUI_MICRO.INFO
      - SIMUI.INFO
      - PSPAPP.INFO
```

This job example shows an example of setting the proxies correctly to make the tests work. This job
can be started by setting `PIPELINE_SELECT` to `check_mooc` or just `mooc`.
It uses the `cache` functionality of gitlab in order to cache some files for the next
run of this job. This is useful as this job must be run twice for a complete successful test: the
first time it runs it starts a simulation or a computation with the job ID or the job URL written to
one of the files. The second time the job runs it takes this information from these files to verify
if the calculations, which might take hours to complete, ended successfully.

## Copyright, Funding & Authors
The development of this software was supported by funding to the Blue Brain Project,
a research center of the École polytechnique fédérale de Lausanne (EPFL), from
the Swiss government's ETH Board of the Swiss Federal Institutes of Technology.


Copyright: Copyright (c) 2024 Blue Brain Project/EPFL

Apache-2.0 license
