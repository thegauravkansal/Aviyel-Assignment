# Aviyel-Assignment

## Installation
* Anaconda Software: https://repo.anaconda.com/archive/Anaconda3-2021.05-Windows-x86_64.exe
* Install all packages in attached requirements.txt file
## Database
I have stored data into text and excel files.
## Folders
* <b>logs:</b> Store data_extraction_api script logs.
* <b>data:</b> Store processed and unprocessed raw data.
* <b>analysis:</b> Store channel, playlist and video category analysis results.
<br>`analysis/<keyword>/<category>/<tag level analysis>/`
## Script
* <b>script.py:</b> Will fetch and extract records from the youtube. Take keyword and sample size as input parameters. Can be executed for getting standalone data.
* <b>data_extraction_api.py:</b>  Will fetch and extract records from the youtube. Take keyword and sample size as input parameters in json format. This will help us integrate this with any analysis script.
* <b>Youtube Keyword Analysis.ipynb:</b> Will used for fetched records analysis. We can use data extracted from script.py or we can use data_extraction_api.py for continuous data analysis.
## API Used
* Using youtube-search-python open source API. Not able to use google api because limited requests can be made in a free account.
<br> https://github.com/alexmercerind/youtube-search-python/tree/main/youtubesearchpython/x`x`__future__

Note: This API returns records in a different format the Google API
### Execution Steps for Continuous Analysis:
1. Run  data_extraction_api.py. Note: Port 5000 should be enabled.
2. Open  Youtube Keyword Analysis.ipynb  file in a jupyter notebook and execute the cells in a sequence.
3. Profiling<br>
    1. Set app.config["DEBUG"] = True and uncomment line:215 @flask_profiler.profile().
    2. Open http://127.0.0.1:5000/flask-profiler/ for analysis.
