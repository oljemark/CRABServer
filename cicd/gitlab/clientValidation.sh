#!/bin/bash

set -x
set -euo pipefail

# always run inside ./workdir
export ROOT_DIR=$(dirname "$PWD")
export WORK_DIR=$PWD
pushd "${WORK_DIR}"

# validate env var
# note: $PWD is (default to `./workdir`)
echo "(debug) ROOT_DIR=${ROOT_DIR}"
echo "(debug) WORK_DIR=${WORK_DIR}"
echo "(debug) X509_USER_PROXY=${X509_USER_PROXY}"
echo "(debug) Client_Validation_Suite=${Client_Validation_Suite}"
echo "(debug) CMSSW_release: ${CMSSW_release}"

source "${ROOT_DIR}/cicd/gitlab/setupCRABClient.sh"

{
 
  TMP_BUFFER=$(mktemp -dt )/client_validation.log
  STORAGE_SITE="T2_CH_CERN"
  PROXY=$(voms-proxy-info -path 2>&1)
  OUTPUTDIR="$PWD/logdir"
  TASK_TO_SUBMIT="crabConfiguration.py"
  TASK_DIR="${ROOT_DIR}/test/clientValidationTasks"

  #list of commands to execute for full testing (sl7/8)
  FULL_TEST=(createmyproxy checkusername checkwrite tasks preparelocal status report getlog getoutput recover)
  #list of commands to execute on sl6
  SL6_TESTS=(status checkusername)
  
  #${TEST_LIST} comes from Jenkins and is used to specify which testing should be done: PR_TEST or FULL_TEST
  # Get configuration from CMSSW_release   
  
  CONFIG_LINE="$(grep "CMSSW_release=${CMSSW_release};" "${ROOT_DIR}"/test/testingConfigs)"
  SCRAM_ARCH="$(echo "${CONFIG_LINE}" | tr ';' '\n' | grep SCRAM_ARCH | sed 's|SCRAM_ARCH=||')"
  # see https://github.com/dmwm/WMCore/issues/11051 for info about SCRAM_ARCH formatting
  singularity="$(echo "${SCRAM_ARCH}" | cut -d"_" -f 1 | tail -c 2)"
  export SCRAM_ARCH singularity  
  if [ "X${singularity}" == X6 ] ; then export TEST_LIST=SL6_TESTS; fi
  if [ "X${singularity}" == X7 ] ; then export TEST_LIST=FULL_TEST; fi
  if [ "X${singularity}" == X8 ] ; then export TEST_LIST=FULL_TEST; fi
  TEST_TO_EXECUTE=${TEST_LIST}[@]

  function logMsg() {
    local kind=$1
    local msg=$2
    case $kind in
    OK)
      printf "$kind %-80s\n" "$msg"
      ;;
    WARNING)
      printf "$kind %-80s\n" "$msg"
      ;;
    FAILED)
      printf "$kind %-80s\n" "$msg"
      ;;
    esac
}

  function checkThisCommand() {
    set +euo pipefail
    local cmd="$1"
    local parms="$2"

    if [[ ! " ${!TEST_TO_EXECUTE} " =~ " ${cmd} " ]]; then
         :
    else
      echo "____________"
    	echo -ne "TEST_COMMAND: crab $cmd $parms \n" 
    	crab --debug $cmd $parms 2>&1 > $TMP_BUFFER
    	if [ $? != 0 ]; then
      		error=`cat $TMP_BUFFER`
      		if [[ $error == *"Cannot retrieve the status_cache file"* ]]; then
        		echo "TEST_RESULT: `logMsg WARNING 'This is a warning message'`"
      		else
        		echo "TEST_RESULT: `logMsg FAILED 'This is a failure message'`"
      		fi
    	else
          
      		echo "TEST_RESULT: `logMsg OK 'This is a status ok message'`"
    	fi
    	echo "TEST_MESSAGE:"
    	cat $TMP_BUFFER
    	echo -e "____________\n"
     fi
     set -euo pipefail
  }

  # check for a valid proxy
  function checkProxy() {
    # Use the X509_USER_PROXY value that was set in the .gitlab-ci.yml script
    if [ -z "$X509_USER_PROXY" ]; then
        echo "Fatal Proxy error: No proxy found or the X509_USER_PROXY environment variable is not set. Please ensure a valid proxy is available."
        exit 1
    fi

    # Verify that the proxy path is valid
    PROXY_INFO=$(voms-proxy-info -path 2>&1)
    if echo "$PROXY_INFO" | grep -q 'Proxy not found'; then
        echo "Fatal Proxy error: No proxy found at $X509_USER_PROXY. Please create one to proceed with the validation."
        exit 1
    fi

    # Display all proxy information
    voms-proxy-info -all
}

  TMP_PARM1=("")
  function checkCmdParam() {
    cmdArgs=($(crab "$1" -h | sed -n '/--help/,$p' | grep '^  -' | awk '{print $1}' | xargs | sed 's/-h,//g'))
    TMP_PARM1="${cmdArgs[@]}"
  }

  USETHISPARMS=()
  INITPARMS=()
  function feedParms() {
    local parms=($INITPARMS)
    local values=($1)
    parmsToUse=""
    local idx=0
    for p in "${parms[@]}"; do
      vtp=''
      if [[ "$p" == *'|'* ]]; then
        vtp=$(echo $p | cut -d'|' -f${values[$idx]} | sed "s|'||g")
      else
        vtp=$(echo "$p=${values[$idx]} ")
      fi
      idx=$((idx + 1))
      parmsToUse="$parmsToUse $vtp"
    done
    #echo $parmsToUse
    USETHISPARMS+=("$parmsToUse")
  }

  checkProxy

  ##################################################
  # START CRABCLIENT VALIDATION
  ##################################################

  ### 1. test crab createmyproxy -h, --days=100
  USETHISPARMS=()
  INITPARMS="--days"
  feedParms "100"
  for parm in "${USETHISPARMS[@]}"; do
       checkThisCommand createmyproxy "$parm"
  done

  ### 2. test crab checkusername -h, --proxy=PROXY
  USETHISPARMS=()
  INITPARMS="--proxy"
  feedParms "$PROXY"
  checkThisCommand checkusername "${USETHISPARMS[@]}"


  ### 3. crab checkwrite --site=SITENAME --proxy=PROXY --checksum=CHECKSUM
  USETHISPARMS=()
  INITPARMS="--site --proxy"
  feedParms "$STORAGE_SITE $PROXY"
  INITPARMS="--site --proxy --checksum"
  feedParms "$STORAGE_SITE $PROXY yes"
  for parm in "${USETHISPARMS[@]}"; do
      checkThisCommand checkwrite "$parm"
  done


  ### 4. test crab tasks --days=3 --status=PARAMS --proxy=PROXY
  USETHISPARMS=()
  INITPARMS="--days --status --proxy --instance"
  PARAMS=(NEW WAITING HOLDING QUEUED SUBMITTED SUBMITFAILED KILLED KILLFAILED RESUBMITFAILED FAILED)
  for st in "${PARAMS[@]}"; do
    feedParms "1 $st $PROXY $REST_Instance"
  done
  for parm in "${USETHISPARMS[@]}"; do
    checkThisCommand tasks "$parm"
  done


  ##################################################
  # START CHECKING SUBMITTED TASK'S STATUS
  ##################################################

  TASKTOTRACK=`cat ${WORK_DIR}/submitted_tasks_CV_${CI_PIPELINE_ID}_${CMSSW_release}`
  PROJDIR=`crab remake --task=$TASKTOTRACK --instance=$REST_Instance --proxy=$PROXY| grep 'Finished remaking project directory' | awk '{print $6}'`

  ### 5. test crab preparelocal --proxy=PROXY --dir=PROJDIR
  USETHISPARMS=()
  INITPARMS="--proxy --dir"
  feedParms "$PROXY $PROJDIR"
  for param in "${USETHISPARMS[@]}"; do
    checkThisCommand preparelocal "$param"
  done


  ### 6. test crab status --proxy=PROXY --dir=PROJDIR --long --verboseErrors  --sort=SORTING
  USETHISPARMS=()
  INITPARMS="'--long|--verboseErrors|' --proxy --dir"
  for opt in 1 2 3 4; do
    feedParms "$opt $PROXY ${PROJDIR}"
  done
  INITPARMS="--sort  --proxy --dir"
  SORTING=('state' 'site' 'runtime' 'memory' 'cpu' 'retries' 'waste' 'exitcode')
  for st in "${SORTING[@]}"; do
    feedParms "$st $PROXY ${PROJDIR}"
  done
  for param in "${USETHISPARMS[@]}"; do
    checkThisCommand status "$param"

  done

  ### 6b. test  crab status --proxy=PROXY --task=TASKNAME --instance=INSTANCE
  USETHISPARMS=()
  INITPARMS="--proxy --task --instance"
  feedParms "$PROXY $TASKTOTRACK $REST_Instance"
  for param in "${USETHISPARMS[@]}"; do
    checkThisCommand status "$param"
  done

  ### 7. test crab report --proxy=PROXY --dir=PROJDIR --outputdir=OUTPUTDIR
  USETHISPARMS=()
  INITPARMS="--outputdir --proxy --dir"
  feedParms "$OUTPUTDIR $PROXY $PROJDIR"
  for param in "${USETHISPARMS[@]}"; do
    checkThisCommand report "$param"
  done


  ### 8. test crab getlog --quantity=QUANTITY  --short --outputpath=URL --dump --xrootd
  # --jobids=JOBIDS --checksum=CHECKSUM --proxy=PROXY --dir=PROJDIR
  USETHISPARMS=()
  INITPARMS="--quantity '--short|' --outputpath '|--dump|--xrootd' --jobids --checksum  --proxy --dir"
  feedParms "2 1 $OUTPUTDIR 2 2,3 yes $PROXY $PROJDIR"
  feedParms "2 2 $OUTPUTDIR 2 2,3 no  $PROXY $PROJDIR"
  for param in "${USETHISPARMS[@]}";do
    checkThisCommand getlog "$param"
  done


  ### 9. test crab getoutput --quantity=QUANTITY --parallel=NPARALLEL --wait=WAITTIME --outputpath=URL
  # --dump --xrootd --jobids=JOBIDS --checksum=CHECKSUM --proxy=PROXY --dir=PROJDIR
  USETHISPARMS=()
  # use --jobids instead of --quantity
  INITPARMS="--parallel --wait --outputpath '|--dump|--xrootd' --jobids --checksum --proxy --dir"
  feedParms "10 4 $OUTPUTDIR 1 2,3 yes $PROXY $PROJDIR"
  feedParms "10 4 $OUTPUTDIR 1 2,3 no  $PROXY $PROJDIR"
  feedParms "10 4 $OUTPUTDIR 2 2,3 yes $PROXY $PROJDIR"
  feedParms "10 4 $OUTPUTDIR 2 2,3 no  $PROXY $PROJDIR"
  feedParms "10 4 $OUTPUTDIR 3 2,3 yes $PROXY $PROJDIR"
  feedParms "10 4 $OUTPUTDIR 3 2,3 no  $PROXY $PROJDIR"
  # use --quantity instead of jobis
  INITPARMS="--quantity --parallel --wait --outputpath '|--dump|--xrootd' --checksum --proxy --dir"
  feedParms "1 10 4 $OUTPUTDIR 1 yes $PROXY $PROJDIR"
  feedParms "3 10 4 $OUTPUTDIR 1 no  $PROXY $PROJDIR"
  for param in "${USETHISPARMS[@]}";do
    checkThisCommand getoutput "$param"
  done

  ### 10. test crab kill --proxy=PROXY --dir=PROJDIR
  USETHISPARMS=()
  INITPARMS="--proxy --dir"
  feedParms "$PROXY $PROJDIR"
  for param in "${USETHISPARMS[@]}"; do
    checkThisCommand kill "$param"
  done
  
  ### 11. test crab recover --proxy=PROXY --dir=PROJDIR
  USETHISPARMS=()
  INITPARMS="--proxy --dir"
  feedParms "$PROXY $PROJDIR"
  for param in "${USETHISPARMS[@]}"; do
    checkThisCommand recover "$param"
  done

  ### 12. test  crab recover --proxy=PROXY --task=TASKNAME --instance=INSTANCE
  USETHISPARMS=()
  INITPARMS="--proxy --task --instance"
  feedParms "$PROXY $TASKTOTRACK $REST_Instance"
  for param in "${USETHISPARMS[@]}"; do
    checkThisCommand recover "$param"
  done

} 2>&1 | tee ${WORK_DIR}/client-validation.log
popd

