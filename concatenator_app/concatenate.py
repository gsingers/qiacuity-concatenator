import traceback

from flask import (
    Blueprint, request, abort, current_app, jsonify, render_template, current_app
)
import os
import glob
import pandas as pd
import numpy as np
import math
import shutil
import datetime

bp = Blueprint('concatenate', __name__, url_prefix='/concatenate')


# Files are either:
#   "","Sample/NTC/Control","Reaction Mix","Target","IC","Control type","Concentration (copies/?L)","CI (95%)","Partitions (valid)","Partitions (positive)","Partitions (negative)","Threshold"
# or
#   "Well","Hyperwell","Categories","Group","Count","Total","Volume"
#

# we need the paired analysis file.  Name format is: plate-*-analysis.csv
def get_analysis_name(plate_id):
    folder = current_app.config["UPLOAD_FOLDER"]
    the_glob = "%s/%s*analysis.csv" % (folder, plate_id)
    print("Looking for analysis named: %s" % the_glob)
    files = glob.glob(the_glob)
    #should just be one
    if len(files) == 1:
        return files[0].replace(folder, "")
    else:
        return None


def process_files(file_names, upstream_dilution_factor, ul_into_reaction, reaction_volume, number_partitions, assay_map):
    print(file_names)
    analysis_frames = []
    occupancy_frames = []
    for file in file_names:
        print("Processing file: %s" % file)
        # Get the plate id
        if file.find("-"):
            plate_id = file.split("-")[0]
            print("Plate_id: %s" % plate_id)
            df = load_data_frame(current_app.config["UPLOAD_FOLDER"], file)
            if df is not None:
                try:
                    df["Plate ID"] = plate_id # both analysis and occupancy need plate_id
                    #print(df.keys())
                    # NOTE: hardcoding a column name as an indicator of file type
                    if "Reaction Mix" in df.keys():
                        print("Processing Analysis file %s" % file)
                        df = process_analysis_file(df, number_partitions, plate_id, reaction_volume, ul_into_reaction,
                                              upstream_dilution_factor)
                        analysis_frames.append(df)
                    elif "Categories" in df.keys():
                        print("Processing Occupancy file: %s" % file)

                        analysis_name = get_analysis_name(plate_id)
                        if analysis_name is not None:
                            analysis_df = load_data_frame(current_app.config["UPLOAD_FOLDER"], analysis_name)
                            analysis_df["Plate ID"] = plate_id
                            analysis_df.rename(columns={"Unnamed: 0": "Well"}, inplace=True)
                            df = process_occupancy_file(df, analysis_df, assay_map)
                            occupancy_frames.append(df)
                        else:
                            print("Could not find matching analysis file for Plate ID: %s" % plate_id)
                            return abort(400)
                except TypeError as e:
                    print(f"Could not process file {file} due to exception {e}")
                    traceback.print_exception(type(e), e, e.__traceback__)

                    return abort(400, file)

        else:
            print("Can't find plate id or otherwise don't know how to process file: %s" % file)
            return abort(415)
    print("Concatenating %s files" % len(analysis_frames))
    final_analysis = None
    final_occupancy = None
    if len(analysis_frames) > 0:
        final_analysis = pd.concat(analysis_frames)
    if len(occupancy_frames) > 0:
        final_occupancy = pd.concat(occupancy_frames)
    return final_analysis, final_occupancy


def load_data_frame(folder, file):
    try:
        # try with Windows-1252 due to `<B5>`
        df = pd.read_csv("%s/%s" % (folder, file), skiprows=1, encoding="Windows-1252")
    except:
        # try with default encoding
        df = pd.read_csv("%s/%s" % (folder, file), skiprows=1)
    return df


def replace_map(input, assay_map):
    # we have a string like GREEN-YELLOW-RED-CRIMSON
    # and a map of key value pairs
    splits = input.split("-")
    result = ""
    sz = len(splits)
    for idx, item in enumerate(splits):
        result += assay_map.get(item, item) # if we can't find a replacement, keep what we have
        if idx < sz - 1:
            result += "-"
    return result    

def process_occupancy_file(occupancy_df, analysis_df, assay_map):
    occupancy_df["Categories"] = occupancy_df["Categories"].apply(lambda x: replace_map(x, assay_map))
    # we need to use the plate_id and the well to find the sample name in the "analysis" file
    sub_a_df = pd.DataFrame(
         {
             "Plate ID": analysis_df["Plate ID"],
             "Well": analysis_df["Well"],
             "Sample/NTC/Control": analysis_df["Sample/NTC/Control"],
         }
     )
    merge = pd.merge(occupancy_df, sub_a_df.drop_duplicates(), on=["Plate ID", "Well"], how="left")
    return merge

def process_analysis_file(df, number_partitions, plate_id, reaction_volume, ul_into_reaction, upstream_dilution_factor):
    # do some clean up
    print(df.dtypes)
    df.rename(columns={"Unnamed: 0": "Well"}, inplace=True)
    # handle "-"
    df["CI (95%)"] = df["CI (95%)"].replace("-", np.nan)
    df["Concentration (copies/µL)"] = df["Concentration (copies/µL)"].replace("n.a.", np.nan)
    df["Concentration (copies/µL)"] = df["Concentration (copies/µL)"].astype(float)
    # strip %
    df["CI (95%)"] = df['CI (95%)'].str.rstrip('%').astype('float') / 100.0

    # User Provided
    df["Upstream DF"] = upstream_dilution_factor
    df["uL into Reaction"] = ul_into_reaction
    df["Reaction Volume"] = reaction_volume
    # Formulas
    # =G2*(K2/J2)*I2
    # Note: Concentration (copies/muL) has a different name on sheet 2 than on sheet 1.
    # TODO: Confirm with Rox what she wants it called.
    df["Concentration in Sample tube (cp/uL)"] = df["Concentration (copies/µL)"] * (
                reaction_volume / ul_into_reaction) * upstream_dilution_factor
    # =L2*(H2/2)
    # Note: CI 95% is has a different name on sheet 2
    df["95% CI (cp/uL)"] = df["Concentration in Sample tube (cp/uL)"] * (df["CI (95%)"] / 2)
    # =(N2/Sheet1!Q$1)*
    df["Valid Partitions (%)"] = (df["Partitions (valid)"] / number_partitions) * 100
    # =Q2/N2
    df["E"] = df["Partitions (negative)"] / df["Partitions (valid)"]
    df["Lambda"] = - np.log(df["E"])  # this is the natural log, Python's default base for log is e
    # =((T2^U$1)*EXP(-T2))/FACT(U$1)
    # these values to the power of 0 and 1 as well as factorial of 0 and 1 are kinda silly, but they
    # are the formula I was given.  I've parameterized them as "factor" below
    factor = 0
    df["0.00"] = ((np.power(df["Lambda"], factor)) * np.exp(-df["Lambda"])) / np.math.factorial(factor)
    factor = 1
    df["1.00"] = ((np.power(df["Lambda"], factor)) * np.exp(-df["Lambda"])) / np.math.factorial(factor)
    df["+1"] = 1 - df["0.00"] - df["1.00"]
    # =(U2)*$N2
    df["Partitions with 0 molecules"] = df["0.00"] * df["Partitions (valid)"]
    df["Partitions with 1 molecule"] = df["1.00"] * df["Partitions (valid)"]
    df["Partitions with >1 molecules"] = df["+1"] * df["Partitions (valid)"]
    return df


def move_files(file_names, completed_folder):
    # move the files to completed_folder/date/
    sub_folder = "%s" % datetime.datetime.now().strftime("%b_%d_%Y_%H_%M_%S")
    try:
        os.mkdir(completed_folder)
    except:
        pass
    try:
        os.mkdir("%s/%s" % (completed_folder, sub_folder))
    finally:
        pass
    for file in file_names:
        from_file = "%s/%s" % (current_app.config["UPLOAD_FOLDER"], file)
        to_file = "%s/%s/%s" % (completed_folder, sub_folder, file)
        print("Moving %s to %s" % (from_file, to_file))
        shutil.move(from_file, to_file)


@bp.route('/process', methods=['POST'])
def process():
    if request.method == 'POST':  # a query has been submitted
        file_names = request.form.getlist('file')
        assay_map_raw = request.form["assay_map"] # key=value, one per line
        assay_map = {}
        if assay_map_raw is not None and len(assay_map_raw) > 0:
            splits = assay_map_raw.split("\n")
            if splits is not None and len(splits) > 0:
                assay_map = dict(item.strip().split("=") for item in splits)
                print(assay_map)


        upstream_dilution_factor = float(request.form.get("upstream_dilution_factor", -1, type=float))
        ul_into_reaction = float(request.form.get("ul_into_reaction", -1, type=float))
        reaction_volume = float(request.form.get("reaction_volume", -1, type=float))
        number_partitions = int(request.form.get("number_partitions", -1, type=int))
        analysis_output = request.form['analysis_output_name']
        occupancy_output = request.form['occupancy_output_name']
        analysis_df, occupancy_df = process_files(file_names,  upstream_dilution_factor,
                                                  ul_into_reaction, reaction_volume, number_partitions, assay_map)
        analysis_full_name = "%s/%s" % (current_app.config["RESULTS_FOLDER"], analysis_output)
        occupancy_full_name = "%s/%s" % (current_app.config["RESULTS_FOLDER"], occupancy_output)
        if analysis_df is not None:
            print("Writing results to %s" % analysis_full_name)
            analysis_df.to_csv(analysis_full_name, index=False)
        if occupancy_df is not None:
            print("Writing occupancy results to %s" % occupancy_full_name)
            occupancy_df.to_csv(occupancy_full_name, index=False)
        # now that we've processed everything, let's move it to the completed folder
        move_files(file_names, current_app.config["COMPLETED_FOLDER"])
        results = os.listdir(current_app.config["RESULTS_FOLDER"])
        return render_template("results.jinja2", results=results, files=file_names, analysis_results_file=analysis_full_name,
                           occupancy_results_file=occupancy_full_name)

    return render_template("error.jinja2", request=request)


@bp.route('/select_files', methods=['GET'])
def select_files():
    files = os.listdir(current_app.config["UPLOAD_FOLDER"])
    files.sort()
    return render_template("select_files.jinja2", files=files)