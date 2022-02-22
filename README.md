# QIAcuity Concatenator

# CAVEAT EMPTOR

1. I am not a geneticist, but my sister is.  From time to time, I help her with data processing by writing small tools that reduce her drudgery work.
1. I make no warranties about this work.  I am open sourcing it in case it is useful for others.
1. I have only tested this on a Mac.
1. I am not a UI person.  ;-)
1. It's highly doubtful I'll take pull requests on this    

# Intro

A simple user interface and processing layer to concatenate together large numbers of files that come from 
the QIAGEN QIAcuity instrument and do some basic calculations on them.

It is primarily designed to be run locally and interacted with via your browser.

# Prerequisites

1. Python 3.x (I've only tested on 3.9.7)
1. Familiarity with using the command line.

## Optional

Some way of managing your Python virtual environments

1. [Pyenv](https://github.com/pyenv/pyenv)
1. [Pyenv-virtualenv](https://github.com/pyenv/pyenv)
  

# Installing and Running

## Pyenv (Optional)


1. `pyenv install 3.9.7`
1. `pyenv virtualenv 3.9.7 qiacuity`

## From the Command Line 

1. Clone this repository
1. `pip install -r requirements.txt`
1. `export FLASK_APP=concatenator_app`
1. OPTIONAL: If you want to change where data is stored (defaults are provided)
    1. export UPLOADS_FOLDER=/path/to/your/uploads
    1. export COMPLETED_FOLDER=/path/to/your/completed 
    1. export RESULTS_FOLDER=/path/to/your/results
1. `flask run`

## In your browser

1. `http://localhost:5000`


# Using

The basic workflow is:

1. Provide input data, using one of two ways: 
    1. Upload the files you want to merge.  Two CSV header  types are supported: 
        1. Analysis files.  The header must be: `"","Sample/NTC/Control","Reaction Mix","Target","IC","Control type","Concentration (copies/muL)","CI (95%)","Partitions (valid)","Partitions (positive)","Partitions (negative)","Threshold"`
            1. Note: the empty first column name is the Well.  The program will try to auto-detect and replace that.
        1. Occupancy files. The header must be: `"Well","Hyperwell","Categories","Group","Count","Total","Volume"`
    1. Since this is running locally on your machine, you can also bulk copy data into the `./data/uploads` directory, as in `cp /path/to/csv_files /path/to/this/project/data/uploads` or using whatever file viewer tool you want (e.g. Finder on the Mac)
1.  Click the `Start Concatenator` link (e.g. http://localhost:3000/concatenate/select_files)
1. Fill in the form values and select the files you want to process and hit submit
1. Your results will be in `data/results` and you can download from the app or you can access them via your file viewer or the command line.
    

## Cleaning out old files

This program does no file management.  In order to declutter the file listings, you should periodically move the files out of the `data` directory

