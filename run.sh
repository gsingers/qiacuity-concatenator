usage()
{
  echo "Usage: $0 [-u /path/to/upload/folder] [-c /path/to/completed/folder] [-r /path/to/results/folder]"
  echo "NOTE: Anything in [ ] is considered optional and uses the defaults specified in this file"
  echo "If you are using a Python virtual environment, be sure to activate it first!"
  exit 2
}


UPLOAD_FOLDER="${PWD}/data/uploads"
COMPLETED_FOLDER="${PWD}/data/completed"
RESULTS_FOLDER="${PWD}/data/results"

while getopts ':u:c:r:h' c
do
  case $c in
    u) UPLOAD_FOLDER=$OPTARG ;;
    r) RESULTS_FOLDER=$OPTARG ;;
    c) COMPLETED_FOLDER=$OPTARG ;;
    h) usage ;;
    [?]) usage ;;
  esac
done
shift $((OPTIND -1))

export FLASK_APP=concatenator_app
export FLASK_ENV=development
export UPLOAD_FOLDER=$UPLOAD_FOLDER
export COMPLETED_FOLDER=$COMPLETED_FOLDER
export RESULTS_FOLDER=$RESULTS_FOLDER
echo "If you are using a Python virtual environment, be sure to activate it first!"

echo "Running Concatenator with folders set to: "
echo "Uploads: ${UPLOAD_FOLDER}"
echo "Results: ${RESULTS_FOLDER}"
echo "Completed: ${COMPLETED_FOLDER}"
flask run