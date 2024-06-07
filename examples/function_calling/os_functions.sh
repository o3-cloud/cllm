#!/bin/bash

availableFunctions='
[
    {
        "name": "getOSName",
        "description": "Get the name of the operating system.",
        "parameters": {}
    },
    {
        "name": "getDiskUsage",
        "description": "Get the disk usage.",
        "parameters": {}
    },
    {
        "name": "getSystemUptime",
        "description": "Get the system uptime.",
        "parameters": {}
    },
    {
        "name": "getBatteryStatus",
        "description": "Get the battery status.",
        "parameters": {}
    },
    {
        "name": "getNetworkConfig",
        "description": "Get the network configuration.",
        "parameters": {}
    },
    {
        "name": "getNetworkStats",
        "description": "Get the network statistics.",
        "parameters": {}
    },
    {
        "name": "getSystem",
        "description": "Get the system hardware data.",
        "parameters": {}
    },
    {
        "name": "listFiles",
        "description": "List files in a directory.",
        "parameters": {
            "directoryPath": {
                "type": "string",
                "description": "The path of the directory."
            }
        }
    },
    {
        "name": "getFileContents",
        "description": "Get the contents of a file.",
        "parameters": {
            "filePath": {
                "type": "string",
                "description": "The path of the file."
            }
        }
    },
    {
        "name": "getTime",
        "description": "Get the current time.",
        "parameters": {}
    }
]
'
# Check for -l flag
if [[ $1 == "-l" ]]; then
  echo "INSTRUCTIONS: This script provides functions to get information about the operating system."
  echo "You can use the following functions:"
  echo "If a prompt can not be matched with a function, return an empty array"
  echo "$availableFunctions"
  exit 0
fi

getOSName() {
  uname -s
}

getDiskUsage() {
  df -h
}

getSystemUptime() {
  uptime
}

getBatteryStatus() {
  pmset -g batt
}

getNetworkConfig() {
  ifconfig
}

getNetworkStats() {
  netstat -i
}

getSystem() {
  system_profiler SPHardwareDataType
}

# Function to list files
listFiles() {
  params=$(echo $1 | base64 --decode)
  directoryPath=$(echo $params | jq -r '.directoryPath')
  cmd="ls -lh ${directoryPath}"
  echo "Files in ${directoryPath}: $(eval $cmd)"
}

getFileContents() {
  params=$(echo $1 | base64 --decode)
  filePath=$(echo $params | jq -r '.filePath')
  cmd="cat ${directoryPath}"
  echo "Contents of file ${directoryPath}: $(eval $cmd)"
}

getTime() {
  echo "Current time: $(date +"%Y-%m-%d %H:%M:%S")"
}

json=$(cat)

# Parse JSON and execute function
for row in $(echo "$json" | jq -r '.[] | @base64'); do
  _jq() {
    echo ${row} | base64 --decode | jq -r ${1}
  }

  functionName=$(_jq '.functionName')
  parameters=$(_jq '.parameters' | base64)

  # Call the function
  {
    $functionName $parameters
  } || {
    echo "Error: Failed to execute function $functionName"
  }
done